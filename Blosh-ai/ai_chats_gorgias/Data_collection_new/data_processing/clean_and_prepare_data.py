"""
Clean conversation data and prepare JSONL datasets for fine-tuning.

This script processes raw ticket data (both email and chat channels) and:
- Cleans conversation threads by removing automated messages and email debris
- Filters out system/spam senders
- Creates training datasets in JSONL format
- Generates both single-example and multiple-example training files

Based on the cleaning logic from 2. clean_data.ipynb
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


def clean_message_text(message: str) -> str:
    """Clean individual message content - MINIMAL cleaning to preserve authentic voice.
    
    Only removes:
    - Spam scanner notices
    - Image/attachment references
    - Proofpoint URL wrappers
    - Mobile device signatures
    
    Preserves:
    - Team signatures (Met vriendelijke groet, Team Freebird, phone numbers)
    - Greetings and closings
    - All human-written content
    """
    if message is None or pd.isna(message):
        return ""
    
    text = str(message)
    
    # Normalize line endings only
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # ONLY remove actual artifacts/noise - NOT legitimate content
    patterns = [
        # Proofpoint spam scanning notices (at END of messages)
        r'_{5,}\s*This email has been scanned for spam and viruses by Proofpoint.*?report this email as spam\.',
        r'This email has been scanned for spam and viruses by Proofpoint.*?report this email as spam\.',
        
        # Proofpoint URL wrappers (long encoded URLs)
        r'https://urldefense\.proofpoint\.com/v2/url\?u=[^\s]+',
        
        # Image/attachment references (not actual content)
        r'\[cid:[^\]]+\]',
        r'\[image\d+\.(?:jpeg|jpg|png|gif)\]',
        
        # Mailto links (formatting artifact)
        r'<mailto:[^>]+>',
        
        # Mobile device signatures (not human-written)
        r'^\s*Verstuurd vanaf mijn iPhone\s*$',
        r'^\s*Sent from my iPhone\s*$',
        
        # BOM and special invisible characters
        r'',
    ]
    
    # Apply cleaning patterns
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
    
    # Clean up excessive whitespace (more than 3 newlines)
    text = re.sub(r'\n\n\n+', '\n\n', text)
    
    return text.strip()


def clean_conversation_thread(json_text: str) -> str:
    """
    Clean conversation thread by removing automated messages and cleaning message text.
    
    Args:
        json_text: JSON string containing conversation messages
        
    Returns:
        Cleaned JSON string
    """
    if pd.isna(json_text) or not json_text or json_text == '':
        return '[]'
    
    try:
        messages = json.loads(str(json_text))
    except json.JSONDecodeError:
        return '[]'
    
    # Automated message patterns to filter out (ONLY truly automated system messages)
    automated_patterns = [
        "Bedankt dat je contact met ons hebt opgenomen! Je wachttijd bedraagt meer dan 15 minuten.",
        "Bedankt dat je contact met ons hebt opgenomen! We zullen snel contact met je opnemen.",
        "Bedankt voor je geduld. We staan voor je klaar zodra ons team beschikbaar is.",
        "Wacht op livechat",
    ]
    
    cleaned_messages = []
    for msg in messages:
        # Clean the message text
        msg_text = clean_message_text(msg.get("message", ""))
        
        # Skip empty messages
        if not msg_text:
            continue
        
        # Skip automated messages
        if any(pattern in msg_text for pattern in automated_patterns):
            continue
        
        # Create cleaned message object
        cleaned_msg = dict(msg)
        cleaned_msg["message"] = msg_text
        cleaned_messages.append(cleaned_msg)
    
    return json.dumps(cleaned_messages, ensure_ascii=False)


def clean_chat_chains(json_text: str) -> str:
    """
    Remove embedded email chains/quoted content from messages.
    
    Removes:
    - Content after "On [date]... wrote:" patterns
    - Content after "Op [date]... schreef:" patterns  
    - Quoted lines starting with ">"
    - "-----Original Message-----" sections
    
    Args:
        json_text: JSON string containing message data
        
    Returns:
        Cleaned JSON string with email chains removed
    """
    if pd.isna(json_text) or not json_text or json_text == '':
        return '[]'
    
    try:
        messages = json.loads(str(json_text))
    except json.JSONDecodeError:
        return '[]'
    
    # Patterns for detecting quoted/forwarded email content
    email_chain_patterns = [
        # English: "On Mon, Oct 28, 2025 at 10:30 AM, John wrote:"
        r'\bOn\s+\w+,?\s+\w+\s+\d+,?\s+\d{4}.*?wrote:',
        # Dutch: "Op 28 oktober 2025 om 10:30 heeft John geschreven:"
        r'\bOp\s+\d+\s+\w+\s+\d{4}\s+om\s+\d+:\d+.*?(?:heeft|schreef)',
    ]
    
    # Clean each message
    for message in messages:
        if 'message' in message and message['message']:
            original_message = message['message']
            
            # Check for email chain patterns
            for pattern in email_chain_patterns:
                match = re.search(pattern, original_message, re.IGNORECASE | re.DOTALL)
                if match:
                    # Keep only the text BEFORE the email chain
                    cleaned_message = original_message[:match.start()].strip()
                    message['message'] = cleaned_message
                    break
            
            # Also remove lines that start with ">" (quoted text)
            lines = message['message'].split('\n')
            cleaned_lines = []
            for line in lines:
                if not line.strip().startswith('>'):
                    cleaned_lines.append(line)
                else:
                    # Stop at first quoted line (email chain starts here)
                    break
            message['message'] = '\n'.join(cleaned_lines).strip()
            
            # Remove "-----Original Message-----" and everything after
            if '-----Original Message-----' in message['message']:
                message['message'] = message['message'].split('-----Original Message-----')[0].strip()
    
    return json.dumps(messages, ensure_ascii=False)


def recompute_counts(json_text: str) -> tuple[int, int, int]:
    """
    Count customer and agent messages from conversation JSON.
    
    Args:
        json_text: JSON string containing conversation messages
        
    Returns:
        tuple: (customer_count, agent_count, total_count)
    """
    if pd.isna(json_text) or not json_text or json_text == '':
        return 0, 0, 0
    
    try:
        messages = json.loads(str(json_text))
        
        customer_count = sum(1 for msg in messages if msg.get("sender") == "CUSTOMER")
        agent_count = sum(1 for msg in messages if msg.get("sender") == "AGENT")
        total_count = len(messages)
        
        return customer_count, agent_count, total_count
    
    except (json.JSONDecodeError, TypeError):
        return 0, 0, 0


def filter_system_senders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove obvious non-customer system senders by email domain/subject.
    
    Args:
        df: DataFrame with customer_email column
        
    Returns:
        Filtered DataFrame
    """
    if "customer_email" not in df.columns:
        return df
    
    # Patterns for system senders to exclude
    system_patterns = [
        r"noreply",
        r"do-not-reply",
        r"postmaster",
        r"facebookmail",
        r"proofpoint",
        r"mxtoolbox",
        r"reply-\d+_html",
        r"freebirdicons",
        r"blosh",
    ]
    
    pattern = '|'.join(system_patterns)
    mask = ~df["customer_email"].str.contains(pattern, case=False, na=False)
    
    return df[mask]


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean conversations in dataframe and update message counts.
    
    Args:
        df: DataFrame with conversation_thread column
        
    Returns:
        Cleaned DataFrame
    """
    print("Cleaning conversations...")
    df_cleaned = df.copy()
    
    # Apply cleaning functions in sequence
    print("  - Cleaning message text...")
    df_cleaned['conversation_thread'] = df_cleaned['conversation_thread'].astype(str).apply(clean_conversation_thread)
    
    print("  - Removing email chains...")
    df_cleaned['conversation_thread'] = df_cleaned['conversation_thread'].apply(clean_chat_chains)
    
    # Recompute message counts
    print("  - Recomputing message counts...")
    counts = df_cleaned['conversation_thread'].apply(recompute_counts)
    df_cleaned['customer_msg_count'] = [c[0] for c in counts]
    df_cleaned['agent_msg_count'] = [c[1] for c in counts]
    df_cleaned['total_msg_count'] = [c[2] for c in counts]
    
    # Filter: Keep only conversations with at least 1 customer and 1 agent message
    df_cleaned = df_cleaned[(df_cleaned['customer_msg_count'] > 0) & (df_cleaned['agent_msg_count'] > 0)]
    
    print(f"  - Kept {len(df_cleaned)}/{len(df)} conversations with valid messages")
    
    return df_cleaned


def create_training_json(df: pd.DataFrame, output_file: str, multiple_training_examples: bool = False) -> int:
    """
    Create training JSON file from conversation threads for AI model training.
    Ensures the final message is always from the assistant (agent).
    
    Args:
        df: DataFrame with conversation_thread column
        output_file: Output JSONL file path
        multiple_training_examples: If True, create multiple training examples 
                                   from start to each assistant reply. If False, 
                                   use entire conversation as one example.
        
    Returns:
        Number of training examples created
    """
    print(f"Creating {output_file}...")
    print(f"  Mode: {'multiple examples' if multiple_training_examples else 'single example per conversation'}")
    
    training_data = []
    
    for _, row in df.iterrows():
        try:
            messages = json.loads(row['conversation_thread'])
            
            # Skip if no messages
            if not messages:
                continue
            
            # Get customer first name from the row, handle NaN/None values
            customer_firstname = row.get('customer_firstname', '')
            if pd.isna(customer_firstname) or customer_firstname is None:
                customer_firstname = ''
            else:
                customer_firstname = str(customer_firstname).strip()
            
            # Create system message
            system_message = {
                "role": "system",
                "content": f"Je bent Freebird klantenservice. Antwoord vriendelijk en in het Nederlands tegen {customer_firstname}. als de naam leeg is begin dan een aanhef zonder de naam"
            }
            
            if multiple_training_examples:
                # Create multiple training examples - from start to each assistant reply
                conversation = [system_message]  # Start with system message
                has_user_message = False
                
                for msg in messages:
                    role = "user" if msg.get("sender") == "CUSTOMER" else "assistant"
                    content = (msg.get("message", "") or "") \
                        .replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n") \
                        .strip()
                    
                    if content:  # Only add non-empty messages
                        conversation.append({
                            "role": role,
                            "content": content
                        })
                        
                        if role == "user":
                            has_user_message = True
                        
                        # If this is an assistant message, create a training example
                        # Must have at least system + user + assistant AND have seen a user message
                        if role == "assistant" and len(conversation) > 2 and has_user_message:
                            training_data.append({"messages": conversation.copy()})
            else:
                # Original behavior - single training example per conversation
                # Remove last message if it's from customer
                if messages and messages[-1].get("sender") == "CUSTOMER":
                    messages = messages[:-1]
                
                # Skip if no messages remain or doesn't end with agent
                if not messages or messages[-1].get("sender") != "AGENT":
                    continue
                    
                # Convert to training format
                conversation = [system_message]  # Start with system message
                for msg in messages:
                    role = "user" if msg.get("sender") == "CUSTOMER" else "assistant"
                    content = (msg.get("message", "") or "") \
                        .replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n") \
                        .strip()
                    
                    if content:  # Only add non-empty messages
                        conversation.append({
                            "role": role,
                            "content": content
                        })
                
                # Only add if conversation has both user and assistant messages (plus system)
                if len(conversation) > 2:  # At least system + user + assistant
                    training_data.append({"messages": conversation})
                
        except (json.JSONDecodeError, TypeError) as e:
            continue
    
    # Save to JSONL file (one JSON object per line)
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in training_data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"  Created {len(training_data)} training examples")
    return len(training_data)


def main():
    """Main processing function."""
    
    print("="*70)
    print("FREEBIRD DATA CLEANING & TRAINING DATASET PREPARATION")
    print("MINIMAL CLEANING - Preserves authentic voice & signatures")
    print("="*70)
    print()
    
    # Load raw tickets data
    raw_file = "raw_tickets.csv"
    if not Path(raw_file).exists():
        print(f"ERROR: {raw_file} not found!")
        print("Please ensure raw_tickets.csv exists in the current directory.")
        return
    
    print(f"Loading {raw_file}...")
    df = pd.read_csv(raw_file)
    print(f"  Loaded {len(df)} tickets")
    print()
    
    # Show channel distribution
    if 'channel' in df.columns:
        print("Channel distribution:")
        print(df['channel'].value_counts())
        print()
    
    # Filter out system senders
    print("Filtering system senders...")
    df = filter_system_senders(df)
    print(f"  Kept {len(df)} tickets after filtering")
    print()
    
    # Clean all data
    df_cleaned = clean_dataframe(df)
    print()
    
    # Save cleaned data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cleaned_csv = f"cleaned_tickets_{timestamp}.csv"
    df_cleaned.to_csv(cleaned_csv, index=False, encoding="utf-8")
    print(f"Saved cleaned data: {cleaned_csv}")
    print()
    
    # Process CHAT data
    print("="*70)
    print("PROCESSING CHAT DATA")
    print("="*70)
    df_chat = df_cleaned[df_cleaned["channel"] == "chat"].reset_index(drop=True)
    print(f"Found {len(df_chat)} chat conversations")
    
    if len(df_chat) > 0:
        chat_single_file = f"training_chat_single_{timestamp}.jsonl"
        chat_multiple_file = f"training_chat_multiple_{timestamp}.jsonl"
        
        n_chat_single = create_training_json(df_chat, chat_single_file, multiple_training_examples=False)
        n_chat_multiple = create_training_json(df_chat, chat_multiple_file, multiple_training_examples=True)
        
        print()
        print(f"Chat training files created:")
        print(f"  Single: {chat_single_file} ({n_chat_single} examples)")
        print(f"  Multiple: {chat_multiple_file} ({n_chat_multiple} examples)")
    else:
        print("  No chat conversations to process")
    
    print()
    
    # Process EMAIL data
    print("="*70)
    print("PROCESSING EMAIL DATA")
    print("="*70)
    df_email = df_cleaned[df_cleaned["channel"] == "email"].reset_index(drop=True)
    print(f"Found {len(df_email)} email conversations")
    
    if len(df_email) > 0:
        email_single_file = f"training_mail_single_{timestamp}.jsonl"
        email_multiple_file = f"training_mail_multiple_{timestamp}.jsonl"
        
        n_email_single = create_training_json(df_email, email_single_file, multiple_training_examples=False)
        n_email_multiple = create_training_json(df_email, email_multiple_file, multiple_training_examples=True)
        
        print()
        print(f"Email training files created:")
        print(f"  Single: {email_single_file} ({n_email_single} examples)")
        print(f"  Multiple: {email_multiple_file} ({n_email_multiple} examples)")
    else:
        print("  No email conversations to process")
    
    print()
    print("="*70)
    print("PROCESSING COMPLETE!")
    print("="*70)
    print()
    print("Summary:")
    print(f"  Total conversations processed: {len(df_cleaned)}")
    print(f"  Chat conversations: {len(df_chat)}")
    print(f"  Email conversations: {len(df_email)}")
    print()
    print("Output files:")
    print(f"  Cleaned data: {cleaned_csv}")
    if len(df_chat) > 0:
        print(f"  Chat single: {chat_single_file}")
        print(f"  Chat multiple: {chat_multiple_file}")
    if len(df_email) > 0:
        print(f"  Email single: {email_single_file}")
        print(f"  Email multiple: {email_multiple_file}")
    print()


if __name__ == "__main__":
    main()

