# pyrefly: ignore [missing-import]
import streamlit as st
import requests

st.title("EcoTrace-AI: Autonomous Circularity Agent")

facility_context = st.text_area("Facility Context", "Provide context about the facility...")
uploaded_file = st.file_uploader("Upload Waste Image", type=["jpg", "jpeg", "png"])

if st.button("Submit"):
    if uploaded_file is not None and facility_context:
        with st.spinner("Analyzing..."):
            files = {"waste_image": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"facility_context": facility_context}
            try:
                response = requests.post("http://127.0.0.1:8000/api/audit", files=files, data=data)
                if response.status_code == 200:
                    result = response.json()
                    st.success("Analysis Complete!")
                    
                    st.markdown("### Audit Report")
                    st.markdown(result.get("audit_report", "No report generated."))
                    
                    with st.expander("Vision Classification"):
                        st.write(result.get("vision_classification", ""))
                    
                    with st.expander("Legal Context"):
                        st.write(result.get("context_used", ""))
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to the backend: {e}")
    else:
        st.warning("Please provide both Facility Context and an Image.")
