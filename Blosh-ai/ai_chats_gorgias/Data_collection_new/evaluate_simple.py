"""
Simple Model Evaluation - English Report without Quality Analysis
"""
import os
import json
import pandas as pd
from openai import OpenAI
from datetime import datetime
import time

# Read API key
try:
    with open('api_key_temp.txt', 'r') as f:
        api_key = f.read().strip()
except:
    api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    print("ERROR: No API key found!")
    exit(1)

client = OpenAI(api_key=api_key)

# CORRECT Fine-tuned model ID
FINETUNED_MODEL_ID = "ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized:CVTnPZJB"

def translate_to_english(dutch_text):
    """Translate Dutch text to English using GPT"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a translator. Translate the following Dutch text to English. Only provide the translation, no explanations."},
                {"role": "user", "content": dutch_text[:1000]}  # Limit length
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    except:
        return "[Translation not available]"

def get_system_message(customer_name):
    """Generate system message"""
    if customer_name and customer_name.strip() and customer_name != 'nan':
        return f"Je bent Freebird klantenservice. Antwoord vriendelijk en in het Nederlands tegen {customer_name}. als de naam leeg is begin dan een aanhef zonder de naam"
    return "Je bent Freebird klantenservice. Antwoord vriendelijk en in het Nederlands. als de naam leeg is begin dan een aanhef zonder de naam"

def get_ai_response(customer_message, customer_name, model_id):
    """Get response from fine-tuned model"""
    try:
        system_msg = get_system_message(customer_name)
        
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": customer_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def evaluate_model(csv_path, model_id, num_cases=15):
    """Evaluate model with real cases"""
    
    print("="*80)
    print("FINE-TUNED MODEL EVALUATION")
    print("="*80)
    print(f"\nModel ID: {model_id}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test cases: {num_cases}\n")
    
    # Load data
    df = pd.read_csv(csv_path)
    print(f"[OK] Loaded {len(df)} cases from CSV")
    
    # Filter valid cases
    df_valid = df[df['actual_response'].notna() & (df['actual_response'] != '')]
    
    if len(df_valid) < num_cases:
        num_cases = len(df_valid)
    
    # Sample cases
    sample_df = df_valid.sample(n=num_cases, random_state=42)
    
    results = []
    
    for idx, row in enumerate(sample_df.itertuples(), 1):
        print(f"\n[{idx}/{num_cases}] Case {row.ticket_id}...")
        
        # Extract message
        try:
            conversation = json.loads(row.conversation_thread)
            customer_message = conversation[0]['message']
        except:
            customer_message = "Message not available"
        
        customer_name = str(row.customer_firstname) if hasattr(row, 'customer_firstname') else ""
        if customer_name == 'nan':
            customer_name = ""
        
        print(f"  - Translating customer message...")
        customer_message_en = translate_to_english(customer_message)
        
        print(f"  - Getting AI response...")
        ai_response = get_ai_response(customer_message, customer_name, model_id)
        
        print(f"  - Translating AI response...")
        ai_response_en = translate_to_english(ai_response)
        
        print(f"  - Translating actual response...")
        actual_response_en = translate_to_english(row.actual_response)
        
        print(f"  [DONE]")
        
        results.append({
            'case_num': idx,
            'ticket_id': row.ticket_id,
            'subject': row.subject,
            'customer_name': customer_name,
            'customer_message': customer_message,
            'customer_message_en': customer_message_en,
            'actual_response': row.actual_response,
            'actual_response_en': actual_response_en,
            'ai_response': ai_response,
            'ai_response_en': ai_response_en,
            'category': row.contact_reason if hasattr(row, 'contact_reason') else "Unknown",
        })
        
        time.sleep(0.5)
    
    return results

def generate_html_report(results, output_file):
    """Generate simple HTML report in English"""
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fine-Tuned Model Evaluation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 4px solid #3498db; padding-bottom: 15px; margin-bottom: 30px; }}
        h2 {{ color: #34495e; margin-top: 40px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #ecf0f1; }}
        h3 {{ color: #7f8c8d; margin-top: 25px; margin-bottom: 15px; }}
        .meta {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .meta-item {{ display: inline-block; margin-right: 30px; margin-bottom: 10px; }}
        .meta-label {{ font-weight: bold; color: #7f8c8d; }}
        .test-case {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 25px; margin-bottom: 30px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .case-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 20px; border-radius: 8px; margin: -25px -25px 20px -25px; }}
        .case-title {{ font-size: 24px; font-weight: bold; }}
        .case-info {{ margin-top: 10px; opacity: 0.9; font-size: 14px; }}
        .message-box {{ background: #f0f8ff; border-left: 4px solid #3498db; padding: 20px; margin: 15px 0; border-radius: 4px; }}
        .response-box {{ background: #fff8e1; border-left: 4px solid #ffc107; padding: 20px; margin: 15px 0; border-radius: 4px; }}
        .ai-response-box {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 20px; margin: 15px 0; border-radius: 4px; }}
        .category-tag {{ display: inline-block; background: #e3f2fd; color: #1976d2; padding: 4px 12px; border-radius: 4px; font-size: 13px; margin-top: 5px; }}
        .content {{ white-space: pre-wrap; word-wrap: break-word; font-size: 14px; line-height: 1.6; }}
        .footer {{ margin-top: 50px; padding-top: 20px; border-top: 2px solid #ecf0f1; text-align: center; color: #7f8c8d; }}
        .original {{ color: #666; font-size: 12px; margin-top: 10px; padding-top: 10px; border-top: 1px dashed #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Fine-Tuned Model Evaluation Report</h1>
        
        <div class="meta">
            <div class="meta-item">
                <span class="meta-label">Model ID:</span> {FINETUNED_MODEL_ID}
            </div>
            <div class="meta-item">
                <span class="meta-label">Evaluation Date:</span> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            <div class="meta-item">
                <span class="meta-label">Test Cases:</span> {len(results)}
            </div>
            <div class="meta-item">
                <span class="meta-label">Language:</span> English (translated from Dutch)
            </div>
        </div>
        
        <h2>Test Cases</h2>
"""
    
    # Add each test case
    for result in results:
        html += f"""
        <div class="test-case">
            <div class="case-header">
                <div class="case-title">Case {result['case_num']}: {result['subject']}</div>
                <div class="case-info">
                    Ticket #{result['ticket_id']} | Customer: {result['customer_name'] or 'N/A'} | {result['category']}
                </div>
            </div>
            
            <h3>Customer Message</h3>
            <div class="message-box">
                <div class="content">{result['customer_message_en']}</div>
                <div class="original"><strong>Original (Dutch):</strong> {result['customer_message'][:200]}...</div>
            </div>
            
            <h3>Human Agent Response (Actual)</h3>
            <div class="response-box">
                <div class="content">{result['actual_response_en']}</div>
                <div class="original"><strong>Original (Dutch):</strong> {result['actual_response'][:200]}...</div>
            </div>
            
            <h3>AI Model Response (Fine-tuned)</h3>
            <div class="ai-response-box">
                <div class="content">{result['ai_response_en']}</div>
                <div class="original"><strong>Original (Dutch):</strong> {result['ai_response']}</div>
            </div>
        </div>
"""
    
    html += f"""
        <div class="footer">
            <p><strong>Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</strong></p>
            <p>Fine-tuned model: ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized</p>
            <p>Training data: 3,491 real customer conversations</p>
            <p>Freebird Icons & Simple the Brand - Dutch Customer Support</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    """Main evaluation"""
    csv_path = "c:/GitHub/Blosh_fresh/Blosh-ai/ai_chats_gorgias/research/df_mail_with_responses.csv"
    output_file = "EVALUATION_REPORT.html"
    
    print("Starting Fine-Tuned Model Evaluation...")
    print(f"CSV: {csv_path}")
    print(f"Output: {output_file}\n")
    
    try:
        # Run evaluation
        results = evaluate_model(csv_path, FINETUNED_MODEL_ID, num_cases=15)
        
        print("\n" + "="*80)
        print("GENERATING HTML REPORT")
        print("="*80)
        
        # Generate report
        generate_html_report(results, output_file)
        
        print(f"\n[SUCCESS] Evaluation complete!")
        print(f"\nReport saved to: {output_file}")
        print(f"Test cases: {len(results)}")
        print(f"Model: {FINETUNED_MODEL_ID}")
        print(f"\nAll messages translated to English!")
        print(f"\nOpening report in browser...")
        
        # Open report
        import subprocess
        subprocess.Popen(['start', output_file], shell=True)
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

