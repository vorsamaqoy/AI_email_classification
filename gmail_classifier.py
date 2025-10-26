import os
import pickle
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import json
from datetime import datetime
import re

from email_classifier import EmailClassifier
from config.models import create_sample_config

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class EnhancedGmailClassifier:
    def __init__(self, api_key="demo_key_12345"):
        self.api_url = "http://localhost:8000/classify"
        self.api_key = api_key
        self.service = None
        self.results = []
        
    def authenticate_gmail(self):
        creds = None
        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("❌ credentials.json file not found!")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail authentication completed")
        return True
    
    def get_recent_emails(self, count=10):
        try:
            results = self.service.users().messages().list(
                userId='me', 
                maxResults=count,
                q='in:inbox'
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            print(f"Retrieving {len(messages)} emails...")
            
            for message in messages[:count]:
                msg = self.service.users().messages().get(
                    userId='me', id=message['id']
                ).execute()
                
                payload = msg['payload']
                headers = payload.get('headers', [])
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                
                content = self.extract_content(payload)
                
                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'content': content[:800]
                })
            
            return emails
            
        except Exception as e:
            print(f"❌ Error retrieving emails: {e}")
            return []
    
    def extract_content(self, payload):
        content = ""
        
        if payload.get('mimeType') == 'text/plain':
            body_data = payload.get('body', {}).get('data')
            if body_data:
                content = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    body_data = part.get('body', {}).get('data')
                    if body_data:
                        content = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                        break
        
        return content.strip()
    
    def classify_email(self, email_data):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "subject": email_data["subject"],
            "testo_email": email_data["content"], 
            "sender": email_data["sender"]
        }
        
        try:
            print(f"DEBUG: Sending to API: {payload['subject'][:30]}...")
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            print(f"DEBUG: API Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"DEBUG: API Success: {result.get('urgency', 'N/A')}/{result.get('department', 'N/A')}")
                return result
            else:
                error_msg = f"API error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                print(f"DEBUG: API Error: {error_msg}")
                return {"error": error_msg}
                
        except requests.exceptions.ConnectionError as e:
            error_msg = "API not reachable - ensure it's running on localhost:8000"
            print(f"DEBUG: Connection Error: {error_msg}")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"DEBUG: Exception: {error_msg}")
            return {"error": error_msg}
    
    def extract_keywords(self, subject, content, classification):
        keywords = []
        
        try:
            subject_words = re.findall(r'\b\w{4,}\b', subject.lower())
            keywords.extend(subject_words[:3])
            
            if classification.get('urgency') == 'critical':
                keywords.extend(['urgent', 'critical', 'emergency', 'asap'])
            elif classification.get('urgency') == 'high':
                keywords.extend(['important', 'urgent', 'priority'])
            
            if classification.get('department') == 'technical':
                keywords.extend(['server', 'api', 'database', 'system', 'error', 'bug'])
            elif classification.get('department') == 'billing':
                keywords.extend(['payment', 'invoice', 'billing', 'charge', 'money'])
            elif classification.get('department') == 'sales':
                keywords.extend(['demo', 'trial', 'pricing', 'meeting', 'opportunity'])
            
            unique_keywords = list(set(keywords))[:6]
            return unique_keywords
            
        except Exception as e:
            print(f"DEBUG: Error extracting keywords: {e}")
            return ['email', 'message']
    
    def generate_gmail_search_queries(self, results_by_category):
        searches = {}
        
        for category, emails in results_by_category.items():
            if not emails:
                continue
            
            all_keywords = []
            for email in emails:
                all_keywords.extend(email.get('keywords', []))
            
            keyword_counts = {}
            for kw in all_keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
            
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            search_terms = [kw[0] for kw in top_keywords]
            
            if search_terms:
                searches[category] = f"({' OR '.join(search_terms)})"
        
        return searches
    
    def generate_html_report(self, timestamp):
        results_by_urgency = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        results_by_department = {
            'technical': [],
            'billing': [],
            'sales': [],
            'support': []
        }
        
        for result in self.results:
            if 'error' not in result:
                urgency = result.get('urgency', 'medium')
                department = result.get('department', 'support')
                results_by_urgency[urgency].append(result)
                results_by_department[department].append(result)
        
        urgency_searches = self.generate_gmail_search_queries(results_by_urgency)
        department_searches = self.generate_gmail_search_queries(results_by_department)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gmail Classification Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 15px; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
        .email-item {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 8px; background: #fafafa; }}
        .email-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .email-subject {{ font-weight: bold; color: #2c3e50; font-size: 1.1em; }}
        .email-meta {{ font-size: 0.9em; color: #7f8c8d; }}
        .classification {{ display: inline-block; padding: 5px 10px; border-radius: 15px; font-size: 0.8em; font-weight: bold; margin: 5px; }}
        .critical {{ background: #e74c3c; color: white; }}
        .high {{ background: #f39c12; color: white; }}
        .medium {{ background: #f1c40f; color: #333; }}
        .low {{ background: #2ecc71; color: white; }}
        .technical {{ background: #9b59b6; color: white; }}
        .billing {{ background: #e67e22; color: white; }}
        .sales {{ background: #1abc9c; color: white; }}
        .support {{ background: #34495e; color: white; }}
        .keywords {{ background: #ecf0f1; padding: 8px; border-radius: 5px; margin: 5px 0; font-size: 0.9em; }}
        .search-query {{ background: #d5dbdb; padding: 10px; border-radius: 5px; font-family: monospace; margin: 10px 0; }}
        .confidence {{ float: right; font-size: 0.9em; color: #7f8c8d; }}
        .section {{ margin: 30px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 Gmail Classification Report</h1>
        <p style="text-align: center; color: #7f8c8d;">Generated on {timestamp}</p>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-number">{len(self.results)}</div>
                <div class="stat-label">Total Emails</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(results_by_urgency['critical'])}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(results_by_urgency['high'])}</div>
                <div class="stat-label">High Priority</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(results_by_department['technical'])}</div>
                <div class="stat-label">Technical</div>
            </div>
        </div>

        <div class="section">
            <h2>🚨 By Urgency Level</h2>
        """
        
        urgency_order = ['critical', 'high', 'medium', 'low']
        for urgency in urgency_order:
            emails = results_by_urgency[urgency]
            if emails:
                html_content += f"""
            <h3>{urgency.title()} Priority ({len(emails)} emails)</h3>
            """
                if urgency in urgency_searches:
                    html_content += f"""
            <div class="search-query">
                <strong>Gmail Search:</strong> {urgency_searches[urgency]}
            </div>
                    """
                
                for email in emails:
                    confidence = email.get('overall_confidence', 0)
                    html_content += f"""
            <div class="email-item">
                <div class="email-header">
                    <div class="email-subject">{email['subject']}</div>
                    <div class="confidence">Confidence: {confidence:.1%}</div>
                </div>
                <div class="email-meta">From: {email['sender'][:50]}</div>
                <div>
                    <span class="classification {email['urgency']}">{email['urgency'].upper()}</span>
                    <span class="classification {email['department']}">{email['department'].upper()}</span>
                </div>
                <div class="keywords"><strong>Keywords:</strong> {', '.join(email.get('keywords', []))}</div>
            </div>
                    """
        
        html_content += """
        </div>

        <div class="section">
            <h2>🏢 By Department</h2>
        """
        
        dept_order = ['technical', 'billing', 'sales', 'support']
        for dept in dept_order:
            emails = results_by_department[dept]
            if emails:
                html_content += f"""
            <h3>{dept.title()} Department ({len(emails)} emails)</h3>
            """
                if dept in department_searches:
                    html_content += f"""
            <div class="search-query">
                <strong>Gmail Search:</strong> {department_searches[dept]}
            </div>
                    """
                
                for email in emails:
                    confidence = email.get('overall_confidence', 0)
                    html_content += f"""
            <div class="email-item">
                <div class="email-header">
                    <div class="email-subject">{email['subject']}</div>
                    <div class="confidence">Confidence: {confidence:.1%}</div>
                </div>
                <div class="email-meta">From: {email['sender'][:50]}</div>
                <div>
                    <span class="classification {email['urgency']}">{email['urgency'].upper()}</span>
                    <span class="classification {email['department']}">{email['department'].upper()}</span>
                </div>
                <div class="keywords"><strong>Keywords:</strong> {', '.join(email.get('keywords', []))}</div>
            </div>
                    """
        
        html_content += """
        </div>

        <div class="section">
            <h2>📋 Quick Gmail Searches</h2>
            <p>Copy these searches into Gmail to find similar emails:</p>
        """
        
        all_searches = {**urgency_searches, **department_searches}
        for category, search in all_searches.items():
            html_content += f"""
            <div class="search-query">
                <strong>{category.title()}:</strong> {search}
            </div>
            """
        
        html_content += """
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def generate_text_report(self, timestamp):
        report = f"""
Gmail Email Classification Report
Generated on: {timestamp}
{'='*50}

SUMMARY:
- Total emails processed: {len(self.results)}
- Critical: {len([r for r in self.results if r.get('urgency') == 'critical'])}
- High priority: {len([r for r in self.results if r.get('urgency') == 'high'])}
- Technical issues: {len([r for r in self.results if r.get('department') == 'technical'])}

DETAILED RESULTS:
"""
        
        for i, result in enumerate(self.results, 1):
            if 'error' not in result:
                report += f"""
{i}. {result['subject'][:60]}...
   From: {result['sender'][:40]}
   Classification: {result['urgency'].upper()} | {result['department'].upper()}
   Confidence: {result.get('overall_confidence', 0):.1%}
   Gmail Keywords: {', '.join(result.get('keywords', []))}
   ---
"""
        
        return report
    
    def run(self, count=10, generate_html=True):
        print("🚀 Enhanced Gmail Email Classifier")
        print("=" * 40)
        
        if not self.authenticate_gmail():
            return
        
        emails = self.get_recent_emails(count)
        if not emails:
            print("❌ No emails found")
            return
        
        print(f"\n📧 Classifying {len(emails)} emails...")
        
        for i, email in enumerate(emails, 1):
            print(f"\nProcessing email {i}/{len(emails)}: {email['subject'][:40]}...")
            
            result = self.classify_email(email)
            
            if "error" not in result:
                result['subject'] = email['subject']
                result['sender'] = email['sender']
                result['date'] = email['date']
                result['keywords'] = self.extract_keywords(
                    email['subject'], 
                    email['content'], 
                    result
                )
                
                self.results.append(result)
                
                urgency = result.get('urgency', 'unknown')
                department = result.get('department', 'unknown')
                confidence = result.get('overall_confidence', 0)
                print(f"✅ {email['subject'][:40]}... → {urgency.upper()}/{department.upper()} (conf: {confidence:.1%})")
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Error: {email['subject'][:40]}... → {error_msg}")
        
        if self.results:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if generate_html:
                html_report = self.generate_html_report(timestamp)
                html_filename = f"gmail_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                
                with open(html_filename, 'w', encoding='utf-8') as f:
                    f.write(html_report)
                
                print(f"\n📄 HTML report generated: {html_filename}")
            
            text_report = self.generate_text_report(timestamp)
            text_filename = f"gmail_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write(text_report)
            
            print(f"📄 Text report generated: {text_filename}")
            
            print(f"\n📊 Results:")
            print(f"   Emails processed: {len(self.results)}")
            
            urgency_counts = {}
            dept_counts = {}
            
            for result in self.results:
                urgency = result.get('urgency', 'unknown')
                department = result.get('department', 'unknown')
                urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
                dept_counts[department] = dept_counts.get(department, 0) + 1
            
            print("   By urgency:", dict(urgency_counts))
            print("   By department:", dict(dept_counts))
        else:
            print("\n❌ No emails classified successfully")
            print("Check that the API is running on localhost:8000")


if __name__ == "__main__":
    classifier = EnhancedGmailClassifier()
    
    try:
        count = int(input("How many emails to classify (default 10)? ") or "10")
    except:
        count = 10
    
    classifier.run(count=count, generate_html=True)