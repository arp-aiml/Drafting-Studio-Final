# test_backend.py
import requests

def run_test():
    url = "http://127.0.0.1:8000/draft/generate"
    payload = {
        "template_type": "gst_show_cause_reply",
        "client_name": "TechCorp India Pvt Ltd",
        "opposite_party": "GST Commissioner, Delhi",
        "facts": "We claimed ITC of 1 Lakh. Supplier filed GSTR-1 but not 3B. We have paid tax to supplier.",
        "tone": "Formal"
    }
    
    print("Sending Request to Backend...")
    response = requests.post(url, json=payload)
    print("\n✅ AI RESPONSE (HTML):\n")
    print(response.json()['content'])

if __name__ == "__main__":
    run_test()