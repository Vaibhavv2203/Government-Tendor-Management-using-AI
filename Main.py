import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from pathlib import Path
import PyPDF2
import glob

# Configure page
st.set_page_config(
    page_title="Tender Analysis System",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'companies' not in st.session_state:
    st.session_state.companies = []
if 'tenders_loaded' not in st.session_state:
    st.session_state.tenders_loaded = False
if 'tender_files' not in st.session_state:
    st.session_state.tender_files = []

# Configuration
TENDERS_FOLDER = "D:\Tendor Project\TENDERS_FOLDER"  # Folder containing all tender PDF files

class TenderAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            st.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return None
    
    def load_all_tenders(self):
        """Load all PDF files from the tenders folder"""
        if not os.path.exists(TENDERS_FOLDER):
            os.makedirs(TENDERS_FOLDER)
            st.warning(f"Created '{TENDERS_FOLDER}' folder. Please add your PDF tender files to this folder.")
            return []
        
        pdf_files = glob.glob(os.path.join(TENDERS_FOLDER, "*.pdf"))
        
        if not pdf_files:
            st.warning(f"No PDF files found in '{TENDERS_FOLDER}' folder. Please add your tender PDF files.")
            return []
        
        tender_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, pdf_path in enumerate(pdf_files):
            filename = os.path.basename(pdf_path)
            status_text.text(f"Loading {filename}...")
            progress_bar.progress((i + 1) / len(pdf_files))
            
            # Extract text from PDF
            text_content = self.extract_text_from_pdf(pdf_path)
            
            if text_content:
                tender_info = {
                    "filename": filename,
                    "filepath": pdf_path,
                    "content": text_content,
                    "file_size": os.path.getsize(pdf_path),
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(pdf_path)).isoformat()
                }
                tender_data.append(tender_info)
        
        progress_bar.empty()
        status_text.empty()
        
        return tender_data
    
    def analyze_tender_relevance(self, company_data, tender_content, tender_filename):
        """Use Gemini API to analyze tender relevance"""
        prompt = f"""
        Analyze the following tender document and determine its relevance to a company with these details:

        COMPANY PROFILE:
        - Services: {', '.join(company_data['services'])}
        - Keywords: {', '.join(company_data.get('keywords', []))}
        - Industry: {company_data.get('industry', 'Not specified')}
        - Geographical Focus: {company_data.get('geographical_focus', 'Not specified')}

        TENDER DOCUMENT: {tender_filename}
        TENDER CONTENT:
        {tender_content[:4000]}  # Limit content to avoid API limits

        Please analyze the tender considering ALL company parameters and provide:

        1. OVERALL RELEVANCE SCORE (0-100): Consider services, keywords, industry alignment, and geographical match
        2. DETAILED SCORING BREAKDOWN:
           - Services Match Score (0-100): How well company services align with tender requirements
           - Keywords Match Score (0-100): How many company keywords appear in the tender
           - Industry Match Score (0-100): How well the tender fits the company's industry
           - Geography Match Score (0-100): Does the tender location match company's geographical focus
        3. MATCHING ELEMENTS:
           - Matching Services: Which specific company services match the tender
           - Matching Keywords: Which company keywords were found in the tender
           - Industry Alignment: How the tender relates to the company's industry
           - Geographic Relevance: Location-based relevance assessment
        4. KEY REQUIREMENTS: Main requirements mentioned in the tender
        5. TENDER SUMMARY: Brief summary of what the tender is about
        6. RECOMMENDATION: Should the company consider bidding (Yes/No/Maybe) and detailed reasoning

        Format your response as JSON with these exact keys:
        - relevance_score
        - services_match_score
        - keywords_match_score
        - industry_match_score
        - geography_match_score
        - matching_services
        - matching_keywords
        - industry_alignment
        - geographic_relevance
        - key_requirements
        - tender_summary
        - recommendation
        - reasoning
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Clean up the response to extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            try:
                analysis = json.loads(json_text)
                return analysis
            except json.JSONDecodeError:
                # Fallback: create structured response from text
                return {
                    "relevance_score": 50,
                    "services_match_score": 40,
                    "keywords_match_score": 30,
                    "industry_match_score": 50,
                    "geography_match_score": 60,
                    "matching_services": ["Analysis needed"],
                    "matching_keywords": ["Manual review needed"],
                    "industry_alignment": "Requires manual assessment",
                    "geographic_relevance": "Location analysis needed",
                    "key_requirements": response_text[:200] + "...",
                    "tender_summary": "Summary extracted from AI response",
                    "recommendation": "Manual review needed",
                    "reasoning": response_text[:500] + "..."
                }
        except Exception as e:
            st.error(f"Error analyzing tender {tender_filename}: {str(e)}")
            return None

def save_companies():
    """Save companies to local storage"""
    with open('companies.json', 'w') as f:
        json.dump(st.session_state.companies, f, indent=2)

def load_companies():
    """Load companies from local storage"""
    if os.path.exists('companies.json'):
        with open('companies.json', 'r') as f:
            st.session_state.companies = json.load(f)

def main():
    st.title("🏢 Tender Analysis System")
    st.markdown("---")
    
    # Load existing companies
    load_companies()

    api_key = "YOUR_API_KEY" #Replace with your API key
    
    # Sidebar for API configuration
    with st.sidebar:
        st.header("📊 System Status")
        
        # Show tender folder status
        if os.path.exists(TENDERS_FOLDER):
            pdf_count = len(glob.glob(os.path.join(TENDERS_FOLDER, "*.pdf")))
            st.metric("PDF Tenders Found", pdf_count)
            if pdf_count == 0:
                st.warning("No PDF files in tenders folder")
        else:
            st.error("Tenders folder not found")
        
        # Show companies count
        st.metric("Companies Added", len(st.session_state.companies))
        
        # Load tenders button
        if st.button("🔄 Reload Tender Files"):
            st.session_state.tenders_loaded = False
            st.session_state.tender_files = []
            st.rerun()
    
    # Main tabs
    tab1, tab2 = st.tabs(["📋 Manage Companies", "🔍 Analyze & Match"])
    
    with tab1:
        st.header("Company Management")
        
        # Add new company
        with st.expander("➕ Add New Company", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                company_name = st.text_input("Company Name")
                industry = st.text_input("Industry", help="e.g., Construction, IT Services, Healthcare")
            with col2:
                company_type = st.selectbox("Company Type", ["Private", "Public", "Partnership", "Sole Proprietorship"])
                geographical_focus = st.text_input("Geographical Focus", help="e.g., Mumbai, Maharashtra, Pan-India, International")
            
            services_input = st.text_area("Services (one per line)", height=120, 
                                        help="Enter each service on a new line")
            
            keywords_input = st.text_area("Keywords (one per line)", height=100,
                                        help="Enter relevant keywords that might appear in tenders")
            
            if st.button("Add Company", type="primary"):
                if company_name and services_input:
                    services = [service.strip() for service in services_input.split('\n') if service.strip()]
                    keywords = [keyword.strip() for keyword in keywords_input.split('\n') if keyword.strip()] if keywords_input else []
                    
                    new_company = {
                        "name": company_name,
                        "type": company_type,
                        "industry": industry.strip() if industry else "",
                        "geographical_focus": geographical_focus.strip() if geographical_focus else "",
                        "services": services,
                        "keywords": keywords,
                        "added_date": datetime.now().isoformat()
                    }
                    
                    st.session_state.companies.append(new_company)
                    save_companies()
                    st.success(f"✅ Company '{company_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Please fill in Company Name and Services")
        
        # Display existing companies
        st.subheader("📋 Existing Companies")
        if st.session_state.companies:
            for i, company in enumerate(st.session_state.companies):
                with st.expander(f"🏢 {company['name']} ({company['type']})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**🏭 Industry:** {company.get('industry', 'Not specified')}")
                        st.write(f"**🌍 Geographical Focus:** {company.get('geographical_focus', 'Not specified')}")
                        st.write(f"**⚙️ Services:** {', '.join(company['services'])}")
                        if company.get('keywords'):
                            st.write(f"**🔑 Keywords:** {', '.join(company['keywords'])}")
                        st.write(f"**📅 Added:** {company['added_date'][:10]}")
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                            st.session_state.companies.pop(i)
                            save_companies()
                            st.rerun()
        else:
            st.info("ℹ️ No companies added yet. Add your first company above!")
    
    with tab2:
        st.header("Tender Analysis & Matching")
        
        if not st.session_state.companies:
            st.warning("⚠️ Please add companies first in the 'Manage Companies' tab.")
            return
        
        if not api_key:
            st.warning("⚠️ Please configure your Gemini API key in the sidebar.")
            return
        
        # Initialize analyzer
        analyzer = TenderAnalyzer(api_key)
        
        # Load tenders if not already loaded
        if not st.session_state.tenders_loaded:
            with st.spinner("Loading tender files from folder..."):
                st.session_state.tender_files = analyzer.load_all_tenders()
                st.session_state.tenders_loaded = True
        
        if not st.session_state.tender_files:
            st.error(f"❌ No tender files found in '{TENDERS_FOLDER}' folder. Please add PDF files to the folder and click 'Reload Tender Files' in the sidebar.")
            return
        
        # Display tender files info
        st.success(f"✅ {len(st.session_state.tender_files)} tender files loaded successfully!")
        
        with st.expander("📄 View Loaded Tender Files"):
            for tender in st.session_state.tender_files:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"📄 **{tender['filename']}**")
                with col2:
                    st.write(f"📏 {tender['file_size']} bytes")
                with col3:
                    st.write(f"📅 {tender['last_modified'][:10]}")
        
        st.markdown("---")
        
        # Company selection
        company_names = [company['name'] for company in st.session_state.companies]
        selected_company = st.selectbox("🏢 Select Company for Analysis", company_names)
        
        if selected_company:
            # Get selected company details
            company_data = next(c for c in st.session_state.companies if c['name'] == selected_company)
            
            st.subheader(f"🔍 Analysis for {selected_company}")
            
            # Display company details in a nice format
            company_info_col1, company_info_col2 = st.columns(2)
            with company_info_col1:
                st.write("**🏭 Industry:**", company_data.get('industry', 'Not specified'))
                st.write("**🌍 Geographical Focus:**", company_data.get('geographical_focus', 'Not specified'))
            with company_info_col2:
                st.write("**📋 Company Type:**", company_data.get('type', 'Not specified'))
                st.write("**📅 Added:**", company_data.get('added_date', '')[:10])
            
            # Display services and keywords
            st.write("**⚙️ Services:**")
            for service in company_data['services']:
                st.write(f"• {service}")
            
            if company_data.get('keywords'):
                st.write("**🔑 Keywords:**")
                keyword_cols = st.columns(3)
                for idx, keyword in enumerate(company_data['keywords']):
                    with keyword_cols[idx % 3]:
                        st.write(f"• {keyword}")
            
            # Analysis settings
            col1, col2 = st.columns(2)
            with col1:
                min_relevance = st.slider("🎯 Minimum Relevance Score", 0, 100, 60, 
                                        help="Only show tenders with relevance score above this threshold")
            with col2:
                max_results = st.number_input("📊 Maximum Results", 1, 50, 10,
                                            help="Maximum number of results to display")
            
            if st.button("🚀 Analyze Tenders", type="primary", use_container_width=True):
                results = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, tender in enumerate(st.session_state.tender_files):
                    status_text.text(f"🔍 Analyzing {tender['filename']}... ({i+1}/{len(st.session_state.tender_files)})")
                    progress_bar.progress((i + 1) / len(st.session_state.tender_files))
                    
                    analysis = analyzer.analyze_tender_relevance(
                        company_data, 
                        tender['content'],
                        tender['filename']
                    )
                    
                    if analysis and analysis.get('relevance_score', 0) >= min_relevance:
                        result = {
                            "tender_filename": tender['filename'],
                            "file_path": tender['filepath'],
                            "file_size": tender['file_size'],
                            "last_modified": tender['last_modified'],
                            "company_name": selected_company,
                            "analysis_date": datetime.now().isoformat(),
                            **analysis
                        }
                        results.append(result)
                
                progress_bar.empty()
                status_text.empty()
                
                # Sort by relevance score
                results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                results = results[:max_results]
                
                if results:
                    st.success(f"🎉 Found {len(results)} relevant tenders!")
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        avg_score = sum(r.get('relevance_score', 0) for r in results) / len(results)
                        st.metric("📊 Avg Relevance", f"{avg_score:.1f}%")
                    with col2:
                        high_relevance = len([r for r in results if r.get('relevance_score', 0) >= 80])
                        st.metric("🔥 High Relevance", high_relevance)
                    with col3:
                        recommended = len([r for r in results if 'yes' in r.get('recommendation', '').lower()])
                        st.metric("✅ Recommended", recommended)
                    with col4:
                        maybe_count = len([r for r in results if 'maybe' in r.get('recommendation', '').lower()])
                        st.metric("🤔 Maybe", maybe_count)
                    
                    st.markdown("---")
                    
                    # Display results
                    for i, result in enumerate(results):
                        score = result.get('relevance_score', 0)
                        
                        # Color coding based on score
                        if score >= 80:
                            score_color = "🟢"
                        elif score >= 60:
                            score_color = "🟡"
                        else:
                            score_color = "🔴"
                        
                        with st.expander(f"{score_color} {result['tender_filename']} - {score}% Relevance"):
                            # Main details
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**📊 Overall Score:** {score}%")
                                st.write(f"**💡 Recommendation:** {result.get('recommendation', 'N/A')}")
                                
                                # Score breakdown
                                st.write("**📈 Score Breakdown:**")
                                st.write(f"  • Services: {result.get('services_match_score', 'N/A')}%")
                                st.write(f"  • Keywords: {result.get('keywords_match_score', 'N/A')}%")
                                st.write(f"  • Industry: {result.get('industry_match_score', 'N/A')}%")
                                st.write(f"  • Geography: {result.get('geography_match_score', 'N/A')}%")
                            
                            with col2:
                                st.write(f"**📋 Tender Summary:** {result.get('tender_summary', 'N/A')}")
                                st.write(f"**📝 Key Requirements:** {result.get('key_requirements', 'N/A')}")
                                st.write(f"**📅 File Modified:** {result['last_modified'][:10]}")
                            
                            # Matching details
                            st.markdown("---")
                            match_col1, match_col2 = st.columns(2)
                            
                            with match_col1:
                                st.write("**🎯 Matching Services:**")
                                matching_services = result.get('matching_services', [])
                                if matching_services and matching_services != ['Analysis needed']:
                                    for service in matching_services:
                                        st.write(f"  • {service}")
                                else:
                                    st.write("  • No specific matches found")
                                
                                st.write("**🔑 Matching Keywords:**")
                                matching_keywords = result.get('matching_keywords', [])
                                if matching_keywords and matching_keywords != ['Manual review needed']:
                                    for keyword in matching_keywords:
                                        st.write(f"  • {keyword}")
                                else:
                                    st.write("  • No keyword matches found")
                            
                            with match_col2:
                                st.write(f"**🏭 Industry Alignment:** {result.get('industry_alignment', 'N/A')}")
                                st.write(f"**🌍 Geographic Relevance:** {result.get('geographic_relevance', 'N/A')}")
                            
                            if result.get('reasoning'):
                                st.write("**🤔 AI Analysis:**")
                                st.write(result['reasoning'][:400] + "..." if len(result['reasoning']) > 400 else result['reasoning'])
                    
                    st.markdown("---")
                    
                    # Download buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        json_str = json.dumps(results, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Download Results as JSON",
                            data=json_str,
                            file_name=f"{selected_company}_tender_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    
                    with col2:
                        df = pd.DataFrame(results)
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📊 Download Results as CSV",
                            data=csv,
                            file_name=f"{selected_company}_tender_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                else:
                    st.info(f"ℹ️ No tenders found matching the minimum relevance criteria of {min_relevance}%. Try lowering the threshold.")

if __name__ == "__main__":
    main()
