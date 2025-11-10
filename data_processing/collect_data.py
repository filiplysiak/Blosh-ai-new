import requests
import pandas as pd
from datetime import datetime
import time
import json

headers = {
    "accept": "application/json", 
    "authorization": "Basic Z2luZ2VyQGJsb3NoLmNvbTo0OTVmMWE3OTQzOGVkOTk5YWNjZTg1MGU4ODJlMWZiY2RhMDhlMTcyY2Y0ODBjMjE2YWFiMDRhZmE4ZTUzMzRi"
}
base_url = "https://freebirdicons.gorgias.com/api"

def make_api_request(url, headers, max_retries=5):
    """Make API request with rate limiting and retry logic"""
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
                print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                wait_time = (2 ** attempt) * 60
                print(f"Rate limit exceeded. Waiting {wait_time} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
        else:
            print(f"API Error {response.status_code}: {response.text}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return response
    
    return response

def extract_mail_tickets(max_tickets=2000):
    """Extract email-channel tickets from Gorgias"""
    
    print("="*60)
    print("FREEBIRD MAIL DATA COLLECTION")
    print("="*60)
    print(f"Extracting up to {max_tickets} email tickets...")
    print()
    start_time = time.time()
    
    all_data = []
    cursor = None
    tickets_processed = 0
    email_found = 0
    
    try:
        while email_found < max_tickets:
            url = f"{base_url}/tickets?limit=100&order_by=created_datetime:desc"
            if cursor:
                url += f"&cursor={cursor}"
                
            print(f"Fetching tickets page (found {email_found} emails, scanned {tickets_processed} total)...")
            response = make_api_request(url, headers)
            
            if response.status_code != 200:
                print(f"Failed to get tickets after retries: {response.text}")
                break
                
            data = response.json()
            tickets = data.get('data', [])
            
            if not tickets:
                print("No more tickets found - reached end of data.")
                break
            
            for ticket in tickets:
                tickets_processed += 1
                
                if email_found >= max_tickets:
                    break
                    
                try:
                    # Only process email tickets
                    if ticket.get('channel') != 'email':
                        continue
                    
                    ticket_id = ticket['id']
                    
                    # Get messages for this ticket
                    messages_url = f"{base_url}/tickets/{ticket_id}/messages"
                    messages_response = make_api_request(messages_url, headers)
                    
                    if messages_response.status_code != 200:
                        print(f"Failed to get messages for {ticket_id} after retries")
                        continue
                        
                    messages_data = messages_response.json()
                    messages = messages_data.get('data', [])
                    
                    # Separate customer and agent messages
                    customer_messages = [m for m in messages if not m.get('from_agent', False)]
                    agent_messages = [m for m in messages if m.get('from_agent', False)]
                    
                    # Only keep if both customer and agent present
                    if not customer_messages or not agent_messages:
                        continue
                    
                    # Create conversation thread as JSON
                    conversation_thread = []
                    for msg in messages:
                        if msg:
                            sender_type = "AGENT" if msg.get('from_agent', False) else "CUSTOMER"
                            message_text = msg.get('body_text', '') or ''
                            
                            message_obj = {
                                "sender": sender_type,
                                "message": message_text,
                                "timestamp": msg.get('created_datetime', ''),
                                "message_id": msg.get('id', '')
                            }
                            conversation_thread.append(message_obj)
                    
                    conversation_thread_json = json.dumps(conversation_thread, ensure_ascii=False)
                    
                    # Customer info
                    customer = ticket.get('customer') or {}
                    
                    # Create row data
                    row_data = {
                        'ticket_id': ticket_id,
                        'subject': ticket.get('subject', ''),
                        'status': ticket.get('status', ''),
                        'channel': ticket.get('channel', ''),
                        'via': ticket.get('via', ''),
                        'language': ticket.get('language', ''),
                        'priority': ticket.get('priority', ''),
                        'spam': ticket.get('spam', False),
                        'customer_email': customer.get('email', ''),
                        'customer_firstname': customer.get('firstname', ''),
                        'customer_lastname': customer.get('lastname', ''),
                        'customer_msg_count': len(customer_messages),
                        'agent_msg_count': len(agent_messages),
                        'total_msg_count': len(messages),
                        'conversation_thread': conversation_thread_json,
                        'created_datetime': ticket.get('created_datetime', ''),
                        'updated_datetime': ticket.get('updated_datetime', ''),
                        'last_message_datetime': ticket.get('last_message_datetime', ''),
                        'last_received_message_datetime': ticket.get('last_received_message_datetime', ''),
                        'closed_datetime': ticket.get('closed_datetime', ''),
                    }
                    
                    all_data.append(row_data)
                    email_found += 1
                    
                    if email_found % 100 == 0:
                        elapsed_time = time.time() - start_time
                        avg_time_per_email = elapsed_time / email_found
                        remaining_emails = max_tickets - email_found
                        estimated_remaining_time = avg_time_per_email * remaining_emails
                        
                        print(f"Processed {email_found} email conversations...")
                        print(f"  Elapsed time: {elapsed_time:.1f}s | Avg time per email: {avg_time_per_email:.2f}s")
                        print(f"  Estimated remaining time: {estimated_remaining_time:.1f}s ({estimated_remaining_time/60:.1f} minutes)")
                        print()
                
                except Exception as e:
                    print(f"Error processing ticket {ticket.get('id', 'unknown')}: {e}")
                    continue
                    
            cursor = data.get('meta', {}).get('next_cursor')
            if not cursor:
                print("No more pages available - reached end of data.")
                break
                
            if email_found >= max_tickets:
                break
    
    except Exception as e:
        print(f"Critical error occurred: {e}")
        print(f"Saving {len(all_data)} email conversations collected so far...")
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    elapsed = time.time() - start_time
    print()
    print("="*60)
    print("COLLECTION COMPLETE")
    print("="*60)
    print(f"Email conversations found: {len(df)}")
    print(f"Total tickets scanned: {tickets_processed:,}")
    print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    print()
    
    # Quick analysis
    if len(df) > 0:
        print("DATA ANALYSIS")
        print("="*60)
        print(f"Total tickets: {len(df)}")
        print()
        print("MESSAGE STATISTICS:")
        print(f"  Average customer messages: {df['customer_msg_count'].mean():.1f}")
        print(f"  Average agent messages: {df['agent_msg_count'].mean():.1f}")
        print(f"  Total messages: {df['total_msg_count'].sum()}")
        print()
        print("TICKET STATUS:")
        print(df['status'].value_counts())
        print()
        print("CHANNELS:")
        print(df['channel'].value_counts())
        print()
    
    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = f"raw_mail_data_{ts}.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"Data saved to: {out_csv}")
    print()
    
    return out_csv

if __name__ == "__main__":
    extract_mail_tickets(max_tickets=2000)
