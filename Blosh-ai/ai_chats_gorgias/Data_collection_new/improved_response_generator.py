"""
Improved Response Generator
Combines all best practices to achieve 70-80% excellent responses WITHOUT retraining
"""

import os
import re
import json
from openai import OpenAI
from datetime import datetime

# Initialize client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
FINETUNED_MODEL_ID = "ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized:CVTnPZJB"

# ============================================================================
# KNOWLEDGE BASE
# ============================================================================

KNOWLEDGE_BASE = {
    'return_policy': """RETOURBELEID:
- 14 dagen retourrecht vanaf levering
- Na 14 dagen is retour NIET mogelijk (geen uitzonderingen)
- Retour aanmelden via website
- Terugbetaling binnen 14 dagen na ontvangst retour""",
    
    'defect_protocol': """DEFECT PROTOCOL:
1. Vraag ALTIJD eerst om foto's
2. "Zou je ons foto's kunnen sturen?"
3. Wacht op foto's voordat je oplossing biedt
4. Geef GEEN kortingscodes zonder goedkeuring""",
    
    'order_numbers': """ORDERNUMMERS:
- Freebird: 102xxxxxx (9 cijfers)
- Simple: 203xxxxx (8 cijfers)
- Vertrouw ordernummer van klant
- Claim NIET dat ordernummer fout is"""
}

# ============================================================================
# BRAND DETECTION
# ============================================================================

def detect_brand(order_number=None, email=None, subject=None):
    """Detect correct brand from available information"""
    # Check order number pattern
    if order_number:
        order_str = str(order_number).strip()
        if order_str.startswith('102') and len(order_str) == 9:
            return "Freebird Icons"
        elif order_str.startswith('203') and len(order_str) == 8:
            return "Simple the Brand"
    
    # Check email or subject
    text = f"{email or ''} {subject or ''}".lower()
    if 'simple' in text:
        return "Simple the Brand"
    
    return "Freebird Icons"  # Default

# ============================================================================
# CONTEXT EXTRACTION
# ============================================================================

def extract_context(customer_message):
    """Extract key context from customer message"""
    message_lower = customer_message.lower()
    
    context = {
        'order_number': None,
        'has_photos': False,
        'mentions_defect': False,
        'mentions_return': False,
        'mentions_late_return': False,
        'asks_question': '?' in customer_message,
        'message_length': len(customer_message)
    }
    
    # Extract order number
    order_match = re.search(r'\b(102\d{6}|203\d{5})\b', customer_message)
    if order_match:
        context['order_number'] = order_match.group(1)
    
    # Detect patterns
    context['has_photos'] = any(word in message_lower for word in 
        ['foto', 'photo', 'afbeelding', 'bijlage', 'attachment'])
    
    context['mentions_defect'] = any(word in message_lower for word in 
        ['defect', 'kapot', 'beschadigd', 'kwaliteit', 'pilt', 'quality', 'broken'])
    
    context['mentions_return'] = any(word in message_lower for word in 
        ['retour', 'return', 'terugsturen', 'terug sturen'])
    
    context['mentions_late_return'] = any(phrase in message_lower for phrase in 
        ['14 dagen', '15 dagen', 'te laat', 'verlopen', 'expired'])
    
    return context

# ============================================================================
# KNOWLEDGE INJECTION
# ============================================================================

def get_relevant_knowledge(context):
    """Get relevant knowledge based on context"""
    knowledge_parts = []
    
    if context['mentions_return'] or context['mentions_late_return']:
        knowledge_parts.append(KNOWLEDGE_BASE['return_policy'])
    
    if context['mentions_defect']:
        knowledge_parts.append(KNOWLEDGE_BASE['defect_protocol'])
    
    if context['order_number']:
        knowledge_parts.append(KNOWLEDGE_BASE['order_numbers'])
    
    return '\n\n'.join(knowledge_parts) if knowledge_parts else ""

# ============================================================================
# ENHANCED SYSTEM PROMPT
# ============================================================================

def build_system_prompt(customer_name, brand, context, knowledge):
    """Build comprehensive system prompt"""
    
    # Build context summary
    context_summary = f"""CONTEXT:
- Klant: {customer_name or 'Niet bekend'}
- Ordernummer: {context['order_number'] if context['order_number'] else 'NIET VERMELD - vraag ernaar als nodig'}
- Foto's bijgevoegd: {'Ja' if context['has_photos'] else 'Nee'}
- Gaat over: {
    'Defect/Kwaliteit' if context['mentions_defect'] else 
    'Retour' if context['mentions_return'] else 
    'Algemene vraag'
}"""

    # Build instructions based on context
    specific_instructions = []
    
    if context['mentions_defect'] and not context['has_photos']:
        specific_instructions.append("⚠️ Klant meldt defect maar GEEN foto's - VRAAG: 'Zou je ons foto's kunnen sturen zodat we dit intern kunnen bekijken?'")
    
    if not context['order_number'] and context['mentions_return']:
        specific_instructions.append("⚠️ Klant wil retour maar GEEN ordernummer - VRAAG: 'Kun je je ordernummer met ons delen?'")
    
    if context['mentions_late_return']:
        specific_instructions.append("⚠️ Klant vraagt over retour na 14 dagen - Beleefd maar duidelijk: niet mogelijk")
    
    instructions_text = '\n'.join(specific_instructions) if specific_instructions else "Geen speciale instructies"
    
    # Build full prompt
    prompt = f"""Je bent {brand} klantenservice medewerker.

{context_summary}

{"RELEVANTE KENNIS:\n" + knowledge if knowledge else ""}

{"ACTIES VOOR DIT BERICHT:\n" + instructions_text if specific_instructions else ""}

ALGEMENE REGELS (ALTIJD VOLGEN):
1. Begin ALTIJD met "Hi {customer_name}," (of "Hi," als naam leeg/onbekend is)
2. Bedank voor bericht: "Bedankt voor je bericht."
3. Als informatie ontbreekt - VRAAG ernaar, maak GEEN aannames
4. Bij defecten - ALTIJD eerst foto's vragen
5. Eindig ALTIJD met:
   "Met vriendelijke groet,
   
   Team {brand}
   020 8081004"

TOON: Vriendelijk, empathisch, behulpzaam maar professioneel

BELANGRIJKSTE REGEL: Als je iets niet zeker weet - vraag om verduidelijking of bied aan intern te overleggen. Verzin NIETS."""

    return prompt

# ============================================================================
# RESPONSE GENERATION
# ============================================================================

def generate_response(customer_message, customer_name="", order_number=None, 
                     email=None, subject=None):
    """Generate improved response"""
    
    # Step 1: Brand detection
    brand = detect_brand(order_number, email, subject)
    
    # Step 2: Context extraction
    context = extract_context(customer_message)
    
    # Update order number from context if not provided
    if not order_number and context['order_number']:
        order_number = context['order_number']
    
    # Step 3: Get relevant knowledge
    knowledge = get_relevant_knowledge(context)
    
    # Step 4: Build system prompt
    system_prompt = build_system_prompt(customer_name, brand, context, knowledge)
    
    # Step 5: Generate response with optimal parameters
    try:
        response = client.chat.completions.create(
            model=FINETUNED_MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": customer_message}
            ],
            temperature=0.3,  # Lower for consistency
            max_tokens=500,
            top_p=0.9,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        generated_text = response.choices[0].message.content
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return None
    
    # Step 6: Post-processing validation and fixes
    final_response, fixes = validate_and_fix_response(
        generated_text, 
        customer_name, 
        brand, 
        order_number,
        context
    )
    
    # Step 7: Quality check
    quality = check_response_quality(final_response, customer_message, context)
    
    return {
        'response': final_response,
        'brand': brand,
        'quality_score': quality['quality_score'],
        'fixes_applied': fixes,
        'warnings': quality['warnings'],
        'approved': quality['approved']
    }

# ============================================================================
# POST-PROCESSING & VALIDATION
# ============================================================================

def validate_and_fix_response(response, customer_name, brand, order_number, context):
    """Validate and auto-fix common issues"""
    fixes = []
    
    # Fix 1: Ensure proper greeting
    if not response.strip().startswith(('Hi ', 'Hallo ', 'Beste ')):
        greeting = f"Hi {customer_name}," if customer_name else "Hi,"
        response = f"{greeting}\n\n" + response
        fixes.append("Added greeting")
    
    # Fix 2: Ensure correct brand signature
    wrong_signatures = {
        "Freebird Icons": ["Team Simple the Brand", "Simple the Brand"],
        "Simple the Brand": ["Team Freebird Icons", "Team Freebird\n020"]
    }
    
    if brand in wrong_signatures:
        for wrong in wrong_signatures[brand]:
            if wrong in response:
                response = response.replace(wrong, f"Team {brand}")
                fixes.append(f"Fixed brand signature")
    
    # Fix 3: Remove false order number errors
    if order_number:
        # Don't claim customer's order number is wrong
        if 'ordernummer klopt niet' in response.lower() or 'ordernummer is niet' in response.lower():
            response = re.sub(r'.*ordernummer.*\(klopt\)?\s*niet.*\n?', '', response, flags=re.IGNORECASE)
            fixes.append("Removed false order number error")
    
    # Fix 4: Remove made-up discount codes
    code_pattern = re.search(r'Code:\s*(\w+\d+)', response)
    if code_pattern:
        code = code_pattern.group(1)
        # If code looks personalized (has name/order), it's likely made up
        if customer_name and customer_name.lower() in code.lower():
            response = re.sub(r'Code:.*?\n', '', response)
            response = re.sub(r'kortingscode.*?\n', '', response, flags=re.IGNORECASE)
            fixes.append("Removed made-up discount code")
    
    # Fix 5: Ensure proper closing
    if "Met vriendelijke groet" not in response:
        response += f"\n\nMet vriendelijke groet,\n\nTeam {brand}\n020 8081004"
        fixes.append("Added closing signature")
    
    return response, fixes

def check_response_quality(response, customer_message, context):
    """Check response quality and flag issues"""
    issues = []
    warnings = []
    
    # Critical checks
    if not response.strip().startswith(('Hi ', 'Hallo ', 'Beste ')):
        issues.append("Missing greeting")
    
    if "Met vriendelijke groet" not in response:
        issues.append("Missing closing")
    
    if not any(team in response for team in ["Team Freebird", "Team Simple"]):
        issues.append("Missing team signature")
    
    # Context-based warnings
    if context['mentions_defect'] and not context['has_photos']:
        if 'foto' not in response.lower() and 'photo' not in response.lower():
            warnings.append("Customer mentions defect but response doesn't ask for photos")
    
    if context['mentions_return'] and not context['order_number']:
        if 'ordernummer' not in response.lower():
            warnings.append("Customer wants return but no order number - response should ask for it")
    
    # General checks
    if len(response) < 50:
        warnings.append("Response seems too short")
    
    if len(response) > 800:
        warnings.append("Response is quite long")
    
    # Calculate quality score
    quality_score = 100
    quality_score -= len(issues) * 30  # Critical issues
    quality_score -= len(warnings) * 10  # Warnings
    
    return {
        'quality_score': max(0, quality_score),
        'issues': issues,
        'warnings': warnings,
        'approved': len(issues) == 0 and quality_score >= 70
    }

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    """Example usage"""
    
    # Test cases from evaluation
    test_cases = [
        {
            'message': "Goedemorgen, Hierbij de foto's van de trui.",
            'name': "Petra",
            'order': None
        },
        {
            'message': "Ik heb 4 truien bij jullie gekocht ordernr 20340520 en 1 trui gaat na 2x dragen al ontzettend pillen. Dat moet toch niet zo zijn met een trui van €99,99?",
            'name': "Petra",
            'order': "20340520"
        },
        {
            'message': "Ik wil graag een deel van bestelling 10243011 retoureren. Nu probeer ik de retourzending aan te melden, maar krijg ik een foutmelding.",
            'name': "Dana",
            'order': "10243011"
        }
    ]
    
    print("="*80)
    print("IMPROVED RESPONSE GENERATOR - TEST")
    print("="*80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n\n{'='*80}")
        print(f"TEST CASE {i}")
        print(f"{'='*80}")
        print(f"\nCustomer: {test['name']}")
        print(f"Message: {test['message'][:100]}...")
        
        result = generate_response(
            customer_message=test['message'],
            customer_name=test['name'],
            order_number=test['order']
        )
        
        if result:
            print(f"\n✅ Generated Response:")
            print(f"Brand: {result['brand']}")
            print(f"Quality Score: {result['quality_score']}/100")
            print(f"Approved: {'✅ Yes' if result['approved'] else '⚠️ Needs Review'}")
            
            if result['fixes_applied']:
                print(f"Fixes Applied: {', '.join(result['fixes_applied'])}")
            
            if result['warnings']:
                print(f"⚠️ Warnings: {', '.join(result['warnings'])}")
            
            print(f"\nResponse:\n{'-'*80}")
            print(result['response'])
        else:
            print("❌ Failed to generate response")
    
    print(f"\n\n{'='*80}")
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()

