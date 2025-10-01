# ==================== src/normalization.py ====================

def normalize_german_text(text):
    """
    Normalizza il testo tedesco per confronti più flessibili
    
    Converte:
    - ae → ä
    - oe → ö  
    - ue → ü
    - ss → ß
    - AE → Ä
    - OE → Ö
    - UE → Ü
    - SS → ß
    
    Args:
        text (str): Testo da normalizzare
        
    Returns:
        str: Testo normalizzato
    """
    if not text:
        return text
    
    # Converti in lowercase per normalizzazione
    normalized = text.lower().strip()
    
    # Sostituzioni per umlaut
    normalized = normalized.replace('ae', 'ä')
    normalized = normalized.replace('oe', 'ö')
    normalized = normalized.replace('ue', 'ü')
    
    # Sostituzione per ß
    normalized = normalized.replace('ss', 'ß')
    
    return normalized


def normalize_for_comparison(text):
    """
    Normalizza il testo per confronti, gestendo sia la forma originale che quella semplificata
    
    Args:
        text (str): Testo da normalizzare
        
    Returns:
        list: Lista di possibili forme normalizzate
    """
    if not text:
        return [text]
    
    # Forma originale
    original = text.strip()
    
    # Forma normalizzata (con umlaut e ß)
    normalized = normalize_german_text(text)
    
    # Se sono diverse, restituisci entrambe
    if original != normalized:
        return [original, normalized]
    else:
        return [original]


def compare_german_words(user_answer, correct_answer):
    """
    Confronta due parole tedesche considerando le varianti di scrittura
    
    Args:
        user_answer (str): Risposta dell'utente
        correct_answer (str): Risposta corretta
        
    Returns:
        bool: True se le parole sono equivalenti
    """
    if not user_answer or not correct_answer:
        return user_answer == correct_answer
    
    # Normalizza entrambe le risposte
    user_variants = normalize_for_comparison(user_answer)
    correct_variants = normalize_for_comparison(correct_answer)
    
    # Controlla se c'è una corrispondenza
    for user_variant in user_variants:
        for correct_variant in correct_variants:
            if user_variant == correct_variant:
                return True
    
    return False
