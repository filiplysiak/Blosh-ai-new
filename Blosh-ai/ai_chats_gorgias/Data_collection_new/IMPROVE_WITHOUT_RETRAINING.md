# How to Improve Model Accuracy WITHOUT Retraining

**Model:** ft:gpt-4.1-mini-2025-04-14:personal:blosh-mail-v3-optimized:CVTnPZJB  
**Current Performance:** 40% excellent, 80% usable  
**Goal:** Increase to 60-70% excellent without retraining

---

## 🎯 Quick Wins (Implement Today)

### 1. **Enhanced System Prompts** ⭐ HIGHEST IMPACT

**Current (Basic):**
```python
system_msg = f"Je bent Freebird klantenservice. Antwoord vriendelijk en in het Nederlands tegen {customer_name}."
```

**Improved (Detailed):**
```python
system_msg = f"""Je bent {BRAND_NAME} klantenservice medewerker.

KLANT: {customer_name}
ORDER: {order_number if order_number else 'Niet bekend'}

BELANGRIJKE REGELS:
1. Begin ALTIJD met "Hi {customer_name}," (of "Hi," als naam leeg is)
2. Eindig ALTIJD met "Met vriendelijke groet,\\n\\nTeam {BRAND_NAME}\\n020 8081004"
3. Als je informatie mist (ordernummer, foto's, details) → VRAAG ernaar, geef geen aannames
4. Bij defecten → ALTIJD eerst foto's vragen voordat je oplossing biedt
5. Retourperiode is 14 dagen - daarna NIET mogelijk
6. Bij twijfel → geef voorzichtige antwoord en bied aan om intern te overleggen

TONE: Vriendelijk, behulpzaam, professioneel maar persoonlijk"""
```

**Expected Improvement:** +15-20% accuracy

---

### 2. **Lower Temperature for Consistency** ⭐

**Current:**
```python
response = client.chat.completions.create(
    model=FINETUNED_MODEL_ID,
    temperature=0.7,  # Too high for customer support
    ...
)
```

**Improved:**
```python
response = client.chat.completions.create(
    model=FINETUNED_MODEL_ID,
    temperature=0.3,  # More consistent, less creative
    max_tokens=500,
    top_p=0.9,        # Focus on most likely responses
    ...
)
```

**Expected Improvement:** +10% consistency

---

### 3. **Brand Detection & Validation** ⭐

Add automatic brand detection to prevent wrong signatures:

```python
def detect_brand(order_number, email_domain=None):
    """Detect correct brand from order number or email"""
    if order_number:
        # Freebird: 102xxxxxx (8 digits starting with 102)
        # Simple: 203xxxxx (7 digits starting with 203)
        if order_number.startswith('102') and len(order_number) == 9:
            return "Freebird Icons"
        elif order_number.startswith('203') and len(order_number) == 8:
            return "Simple the Brand"
    
    # Fallback to email domain
    if email_domain and 'simplethebrand' in email_domain:
        return "Simple the Brand"
    
    return "Freebird Icons"  # Default

def get_enhanced_system_message(customer_name, order_number, email=None):
    """Generate brand-aware system message"""
    brand = detect_brand(order_number, email)
    
    return f"""Je bent {brand} klantenservice medewerker.

KLANT: {customer_name or 'Niet bekend'}
ORDER: {order_number or 'Niet bekend'}
MERK: {brand}

CRUCIALE REGELS:
1. Gebruik ALLEEN "Team {brand}" in je handtekening
2. Als klant vraagt naar defect → ALTIJD eerst vragen: "Zou je ons foto's kunnen sturen?"
3. Als ordernummer ontbreekt → vraag: "Kun je je ordernummer met ons delen?"
4. Bij retour na 14 dagen → beleefd maar duidelijk: periode verlopen
5. Geef GEEN kortingscodes zonder toestemming
6. Bij twijfel → "Laat me dit even intern overleggen en we komen bij je terug"

TONE: Vriendelijk, behulpzaam, empathisch maar professioneel

BELANGRIJK: Maak GEEN aannames. Bij onduidelijkheid → vraag om verduidelijking."""
```

**Expected Improvement:** +10% (eliminates brand confusion)

---

### 4. **Pre-Processing: Extract Context** ⭐

Extract key information before sending to model:

```python
import re

def extract_context(customer_message, ticket_data):
    """Extract key information from message"""
    context = {
        'order_number': None,
        'has_photos': False,
        'mentions_defect': False,
        'mentions_return': False,
        'urgency': 'normal'
    }
    
    # Extract order number
    order_match = re.search(r'\b(102\d{6}|203\d{5})\b', customer_message)
    if order_match:
        context['order_number'] = order_match.group(1)
    
    # Detect mentions
    message_lower = customer_message.lower()
    context['has_photos'] = any(word in message_lower for word in ['foto', 'photo', 'afbeelding', 'bijlage'])
    context['mentions_defect'] = any(word in message_lower for word in ['defect', 'kapot', 'beschadigd', 'quality', 'kwaliteit'])
    context['mentions_return'] = any(word in message_lower for word in ['retour', 'return', 'terugsturen'])
    
    # Urgency detection
    if any(word in message_lower for word in ['urgent', 'snel', 'asap', 'spoed']):
        context['urgency'] = 'high'
    
    return context

def generate_response_with_context(customer_message, customer_name, ticket_data):
    """Generate response with extracted context"""
    context = extract_context(customer_message, ticket_data)
    
    # Build enhanced system message with context
    system_msg = f"""Je bent Freebird klantenservice.

CONTEXT:
- Klant: {customer_name}
- Ordernummer: {context['order_number'] or 'Niet vermeld door klant'}
- Foto's bijgevoegd: {'Ja' if context['has_photos'] else 'Nee'}
- Gaat over: {'Defect' if context['mentions_defect'] else 'Retour' if context['mentions_return'] else 'Algemeen'}

ACTIES GEBASEERD OP CONTEXT:
{'- Klant heeft GEEN ordernummer genoemd → VRAAG ernaar' if not context['order_number'] else ''}
{'- Klant meldt defect maar GEEN foto → VRAAG om foto\'s' if context['mentions_defect'] and not context['has_photos'] else ''}

ANTWOORD REGELS:
1. Begin met "Hi {customer_name},"
2. Bedank voor bericht
3. Als info ontbreekt → vraag erom (geen aannames!)
4. Geef duidelijk antwoord
5. Eindig met handtekening"""

    response = client.chat.completions.create(
        model=FINETUNED_MODEL_ID,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": customer_message}
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    return response.choices[0].message.content
```

**Expected Improvement:** +15% (provides crucial context)

---

### 5. **Post-Processing Validation** ⭐

Add validation and auto-correction after generation:

```python
def validate_and_fix_response(response, customer_name, brand, order_number):
    """Validate and automatically fix common issues"""
    fixes_applied = []
    
    # Fix 1: Ensure proper greeting
    if not response.strip().startswith(('Hi ', 'Hallo ', 'Beste ')):
        response = f"Hi {customer_name},\n\n" + response
        fixes_applied.append("Added greeting")
    
    # Fix 2: Ensure correct brand signature
    wrong_brands = {
        "Freebird Icons": ["Team Simple the Brand", "Simple the Brand"],
        "Simple the Brand": ["Team Freebird", "Freebird Icons"]
    }
    
    if brand in wrong_brands:
        for wrong_brand in wrong_brands[brand]:
            if wrong_brand in response:
                response = response.replace(wrong_brand, f"Team {brand}")
                fixes_applied.append(f"Fixed brand from {wrong_brand} to {brand}")
    
    # Fix 3: Ensure closing
    if "Met vriendelijke groet" not in response:
        response += f"\n\nMet vriendelijke groet,\n\nTeam {brand}\n020 8081004"
        fixes_applied.append("Added closing")
    
    # Fix 4: Validate order number references
    if order_number:
        # Don't claim order number is wrong if customer provided it
        if "ordernummer klopt niet" in response.lower() or "order number is wrong" in response.lower():
            # Remove that sentence
            response = re.sub(r'.*ordernummer.*niet.*klopt.*\n', '', response, flags=re.IGNORECASE)
            fixes_applied.append("Removed false order number error")
    
    # Fix 5: Check for made-up discount codes
    code_match = re.search(r'Code:\s*(\w+\d+)', response)
    if code_match:
        code = code_match.group(1)
        # If code looks like customer-specific (contains name/order)
        if customer_name.lower() in code.lower() or (order_number and order_number in code):
            # Remove it - these are made up
            response = re.sub(r'Code:\s*\w+\d+\n?', '', response)
            fixes_applied.append("Removed made-up discount code")
    
    return response, fixes_applied

# Usage
response = generate_response_with_context(customer_message, customer_name, ticket_data)
response_fixed, fixes = validate_and_fix_response(response, customer_name, brand, order_number)

if fixes:
    print(f"Applied fixes: {', '.join(fixes)}")
```

**Expected Improvement:** +10-15% (catches and fixes errors)

---

## 🎯 Medium-Effort Improvements (Implement This Week)

### 6. **Few-Shot Examples in Context**

Add examples of good responses for edge cases:

```python
def get_system_message_with_examples(customer_name, scenario_type):
    """System message with relevant examples"""
    
    examples = {
        'defect_complaint': """
VOORBEELD - DEFECT KLACHT:
Klant: "Mijn trui pilt na 2x dragen"
Goed antwoord: "Hi [naam], Bedankt voor je bericht. Wat vervelend dat dit gebeurt. Zou je ons foto's kunnen sturen zodat we dit intern kunnen bekijken? Dan komen we met een passende oplossing."
Fout antwoord: "Hier is een kortingscode" ❌ (vraag eerst foto's!)
""",
        'missing_info': """
VOORBEELD - INFO ONTBREEKT:
Klant: "Ik wil retour doen"
Goed antwoord: "Hi [naam], Bedankt voor je bericht. Graag help ik je hiermee. Kun je je ordernummer met ons delen?"
Fout antwoord: "Hierbij een retourlabel" ❌ (vraag eerst ordernummer!)
""",
        'late_return': """
VOORBEELD - TE LATE RETOUR:
Klant: "Kan ik nog retourneren na 15 dagen?"
Goed antwoord: "Hi [naam], Bedankt voor je bericht. Wat vervelend dat de bestelling niet helemaal is wat je verwacht had. Helaas hebben wij een retourtermijn van 14 dagen, na 14 dagen is het niet meer mogelijk een retour te verwerken."
Fout antwoord: "Ja natuurlijk" ❌ (niet mogelijk na 14 dagen!)
"""
    }
    
    example = examples.get(scenario_type, '')
    
    return f"""Je bent Freebird klantenservice.

{example}

KLANT: {customer_name}

Volg de voorbeelden hierboven. Bij twijfel → vraag om meer informatie."""

# Detect scenario type
def detect_scenario(message):
    """Detect what type of scenario this is"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['defect', 'kapot', 'kwaliteit', 'pilt']):
        return 'defect_complaint'
    elif any(word in message_lower for word in ['retour', 'return']) and not any(char.isdigit() for char in message):
        return 'missing_info'
    elif any(word in message_lower for word in ['14 dagen', '15 dagen', 'te laat', 'verlopen']):
        return 'late_return'
    
    return 'general'
```

**Expected Improvement:** +10% for edge cases

---

### 7. **Response Quality Checker (Before Sending)**

Create a quality gate:

```python
def check_response_quality(response, customer_message, context):
    """Check if response meets quality standards"""
    issues = []
    warnings = []
    
    # Critical checks
    if not response.strip().startswith(('Hi ', 'Hallo ', 'Beste ')):
        issues.append("Missing greeting")
    
    if "Met vriendelijke groet" not in response:
        issues.append("Missing closing")
    
    if not any(team in response for team in ["Team Freebird", "Team Simple"]):
        issues.append("Missing team signature")
    
    # Warning checks
    if "defect" in customer_message.lower() and "foto" not in response.lower():
        warnings.append("Customer mentions defect but response doesn't ask for photos")
    
    if len(response) < 50:
        warnings.append("Response seems too short")
    
    if len(response) > 800:
        warnings.append("Response is quite long")
    
    # Check for made-up information
    if re.search(r'Code:\s*\w+', response):
        warnings.append("Response contains discount code - verify this is approved")
    
    # Check for assumptions
    if "ordernummer" not in customer_message.lower() and re.search(r'\d{8,9}', response):
        warnings.append("Response mentions order number customer didn't provide")
    
    quality_score = 100
    quality_score -= len(issues) * 30
    quality_score -= len(warnings) * 10
    
    return {
        'quality_score': max(0, quality_score),
        'issues': issues,
        'warnings': warnings,
        'approved': len(issues) == 0 and quality_score >= 70
    }

# Usage
response = generate_response(customer_message, customer_name)
quality = check_response_quality(response, customer_message, context)

if not quality['approved']:
    print(f"⚠️ Quality Score: {quality['quality_score']}/100")
    print(f"Issues: {quality['issues']}")
    print(f"Warnings: {quality['warnings']}")
    
    # Either regenerate or flag for human review
    if quality['quality_score'] < 50:
        # Flag for human review
        response = "[NEEDS_HUMAN_REVIEW] " + response
```

**Expected Improvement:** +10% (prevents bad responses from going out)

---

### 8. **Knowledge Base Injection (Simple RAG)**

Add relevant knowledge to the prompt:

```python
KNOWLEDGE_BASE = {
    'return_policy': """
RETOURBELEID:
- 14 dagen retourrecht vanaf levering
- Na 14 dagen is retour NIET mogelijk (geen uitzonderingen)
- Retour aanmelden via website: freebirdicons.com/policies/refund-policy
- Terugbetaling binnen 14 dagen na ontvangst retour
""",
    'defect_protocol': """
DEFECT PROTOCOL:
1. Vraag klant om foto's te sturen
2. "Zou je ons foto's kunnen sturen?"
3. Wacht op foto's voordat je oplossing biedt
4. Na foto's → intern overleg
5. Geef GEEN kortingscodes zonder goedkeuring
""",
    'order_numbers': """
ORDERNUMMERS:
- Freebird: 102xxxxxx (9 cijfers, begint met 102)
- Simple: 203xxxxx (8 cijfers, begint met 203)
- Vertrouw ordernummer van klant
- Claim NIET dat ordernummer fout is tenzij duidelijk ongeldig
""",
    'common_issues': """
VEELVOORKOMENDE ISSUES:
1. "Kan niet retourneren" → Check of binnen 14 dagen
2. "Pakket niet ontvangen" → Start onderzoek PostNL
3. "Verkeerd adres" → Check of al verstuurd, zo ja → track&trace aanpassen
4. "Kortingscode werkt niet" → Check welke items, outlet vs regulier
"""
}

def get_relevant_knowledge(customer_message):
    """Get relevant knowledge for this message"""
    message_lower = customer_message.lower()
    relevant = []
    
    if 'retour' in message_lower or '14 dagen' in message_lower:
        relevant.append(KNOWLEDGE_BASE['return_policy'])
    
    if 'defect' in message_lower or 'kapot' in message_lower or 'kwaliteit' in message_lower:
        relevant.append(KNOWLEDGE_BASE['defect_protocol'])
    
    if 'ordernummer' in message_lower or 'order' in message_lower:
        relevant.append(KNOWLEDGE_BASE['order_numbers'])
    
    return '\n'.join(relevant)

def generate_response_with_knowledge(customer_message, customer_name):
    """Generate response with knowledge injection"""
    knowledge = get_relevant_knowledge(customer_message)
    
    system_msg = f"""Je bent Freebird klantenservice.

RELEVANTE KENNIS:
{knowledge}

KLANT: {customer_name}

Gebruik de kennis hierboven om een accuraat antwoord te geven."""

    # Rest of generation...
```

**Expected Improvement:** +15% accuracy on policy questions

---

## 🎯 Advanced Improvements (Implement Next Week)

### 9. **Multi-Step Reasoning (Chain of Thought)**

Make the model think before answering:

```python
def generate_with_reasoning(customer_message, customer_name, context):
    """Generate response with explicit reasoning step"""
    
    # Step 1: Analyze the question
    analysis_prompt = f"""Analyseer dit klantbericht:

"{customer_message}"

Beantwoord:
1. Wat vraagt de klant? (1 zin)
2. Welke informatie ontbreekt? (lijst)
3. Wat is de juiste actie? (1 zin)
4. Welke kennis/beleid is relevant? (lijst)"""

    analysis = client.chat.completions.create(
        model=FINETUNED_MODEL_ID,
        messages=[{"role": "user", "content": analysis_prompt}],
        temperature=0.2,
        max_tokens=200
    ).choices[0].message.content
    
    # Step 2: Generate response based on analysis
    response_prompt = f"""ANALYSE:
{analysis}

KLANT: {customer_name}

Schrijf nu het antwoord aan de klant in het Nederlands. Volg de analyse hierboven."""

    response = client.chat.completions.create(
        model=FINETUNED_MODEL_ID,
        messages=[
            {"role": "system", "content": "Je bent Freebird klantenservice. Schrijf een vriendelijk, accuraat antwoord."},
            {"role": "user", "content": response_prompt}
        ],
        temperature=0.3,
        max_tokens=500
    ).choices[0].message.content
    
    return response, analysis
```

**Expected Improvement:** +10-15% (better reasoning)

---

### 10. **A/B Testing & Dynamic Routing**

Route to best-performing strategies:

```python
class ResponseGenerator:
    def __init__(self):
        self.strategies = {
            'simple': self.generate_simple,
            'enhanced': self.generate_enhanced,
            'with_reasoning': self.generate_with_reasoning
        }
        self.performance = {
            'simple': 0.4,      # 40% quality
            'enhanced': 0.65,   # 65% quality (estimated)
            'with_reasoning': 0.7  # 70% quality (estimated)
        }
    
    def route_to_best_strategy(self, customer_message, context):
        """Route to best strategy based on message complexity"""
        message_lower = customer_message.lower()
        
        # Complex cases → reasoning
        if any(word in message_lower for word in ['defect', 'klacht', 'complaint', 'kwaliteit']):
            return 'with_reasoning'
        
        # Standard cases → enhanced
        if any(word in message_lower for word in ['retour', 'return', 'bestelling']):
            return 'enhanced'
        
        # Simple cases → simple
        return 'simple'
    
    def generate(self, customer_message, customer_name, context):
        """Generate with best strategy"""
        strategy = self.route_to_best_strategy(customer_message, context)
        print(f"Using strategy: {strategy}")
        return self.strategies[strategy](customer_message, customer_name, context)
```

**Expected Improvement:** +10% (uses best method for each case)

---

## 📊 Expected Results Summary

| Improvement | Effort | Impact | Cumulative Score |
|------------|--------|--------|------------------|
| **Baseline** | - | - | **40% excellent** |
| 1. Enhanced System Prompts | Low | +15-20% | **55-60%** |
| 2. Lower Temperature | Low | +5% | **60-65%** |
| 3. Brand Detection | Low | +5% | **65-70%** |
| 4. Pre-Processing Context | Medium | +10% | **75-80%** |
| 5. Post-Processing Validation | Medium | +10% | **85-90%** |
| 6. Few-Shot Examples | Medium | +5% | **90-95%** |
| 7. Quality Checker | Medium | +5% | **95-100%** |

**Realistic Target WITHOUT Retraining: 70-80% excellent responses**

---

## 🚀 Implementation Roadmap

### Week 1: Quick Wins (Target: 60-65% excellent)
- ✅ Day 1-2: Enhanced system prompts + lower temperature
- ✅ Day 3-4: Brand detection & validation
- ✅ Day 5: Post-processing fixes

### Week 2: Medium Improvements (Target: 70-75% excellent)
- ✅ Day 1-2: Pre-processing context extraction
- ✅ Day 3-4: Quality checker implementation
- ✅ Day 5: Few-shot examples for edge cases

### Week 3: Advanced (Target: 75-80% excellent)
- ✅ Day 1-3: Knowledge base injection (RAG)
- ✅ Day 4-5: Multi-step reasoning for complex cases

### Week 4: Optimization (Target: 80%+ excellent)
- ✅ A/B testing different strategies
- ✅ Performance monitoring
- ✅ Fine-tune parameters based on real results

---

## 📝 Ready-to-Use Code Template

Complete implementation combining best practices:

```python
# See next file: improved_response_generator.py
```

---

## ⚡ Start Here (Copy-Paste Ready)

The fastest way to improve TODAY → see `quick_improvements.py`

---

**Created:** October 28, 2025  
**Target:** 70-80% excellent without retraining  
**Estimated Time:** 1-3 weeks to implement all improvements

