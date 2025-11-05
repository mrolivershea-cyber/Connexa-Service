"""
Country Code Normalization
Конвертирует коды стран (US, GB, DE) в полные названия
"""

COUNTRY_CODES = {
    'US': 'United States',
    'GB': 'United Kingdom',
    'CA': 'Canada',
    'AU': 'Australia',
    'DE': 'Germany',
    'FR': 'France',
    'IT': 'Italy',
    'ES': 'Spain',
    'NL': 'Netherlands',
    'SE': 'Sweden',
    'NO': 'Norway',
    'DK': 'Denmark',
    'FI': 'Finland',
    'PL': 'Poland',
    'RU': 'Russia',
    'UA': 'Ukraine',
    'JP': 'Japan',
    'CN': 'China',
    'KR': 'South Korea',
    'IN': 'India',
    'BR': 'Brazil',
    'MX': 'Mexico',
    'AR': 'Argentina',
    'ZA': 'South Africa',
    'NZ': 'New Zealand',
    'SG': 'Singapore',
    'HK': 'Hong Kong',
    'MY': 'Malaysia',
    'TH': 'Thailand',
    'ID': 'Indonesia',
    'PH': 'Philippines',
    'VN': 'Vietnam',
    'TR': 'Turkey',
    'IL': 'Israel',
    'AE': 'United Arab Emirates',
    'SA': 'Saudi Arabia',
    'EG': 'Egypt',
    'KE': 'Kenya',
    'NG': 'Nigeria'
}

def normalize_country(country: str) -> str:
    """
    Конвертировать код страны в полное название
    Если уже полное название - вернуть как есть
    """
    if not country:
        return ''
    
    # Если это код (2 символа)
    if len(country) == 2:
        return COUNTRY_CODES.get(country.upper(), country)
    
    # Если уже полное название
    return country
