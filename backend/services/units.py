"""Unit conversion service for recipe measurements."""

# Conversion factors to a base unit within each category
# Volume: base unit = ml
# Weight: base unit = g
# Temperature: handled separately

VOLUME_TO_ML = {
    'ml': 1.0,
    'milliliter': 1.0,
    'milliliters': 1.0,
    'l': 1000.0,
    'liter': 1000.0,
    'liters': 1000.0,
    'tsp': 4.929,
    'teaspoon': 4.929,
    'teaspoons': 4.929,
    'tbsp': 14.787,
    'tablespoon': 14.787,
    'tablespoons': 14.787,
    'fl oz': 29.574,
    'fluid ounce': 29.574,
    'fluid ounces': 29.574,
    'cup': 236.588,
    'cups': 236.588,
    'pint': 473.176,
    'pints': 473.176,
    'quart': 946.353,
    'quarts': 946.353,
    'gallon': 3785.41,
    'gallons': 3785.41,
}

WEIGHT_TO_G = {
    'g': 1.0,
    'gram': 1.0,
    'grams': 1.0,
    'kg': 1000.0,
    'kilogram': 1000.0,
    'kilograms': 1000.0,
    'oz': 28.3495,
    'ounce': 28.3495,
    'ounces': 28.3495,
    'lb': 453.592,
    'pound': 453.592,
    'pounds': 453.592,
}

# Preferred display units for each system
IMPERIAL_VOLUME = ['tsp', 'tbsp', 'cup', 'pint', 'quart', 'gallon']
METRIC_VOLUME = ['ml', 'l']
IMPERIAL_WEIGHT = ['oz', 'lb']
METRIC_WEIGHT = ['g', 'kg']

# Thresholds for choosing display unit (in base units)
METRIC_VOLUME_THRESHOLDS = [(1000, 'l'), (0, 'ml')]
METRIC_WEIGHT_THRESHOLDS = [(1000, 'kg'), (0, 'g')]
IMPERIAL_VOLUME_THRESHOLDS = [
    (3785.41, 'gallon'), (946.353, 'quart'), (473.176, 'pint'),
    (236.588, 'cup'), (14.787, 'tbsp'), (0, 'tsp'),
]
IMPERIAL_WEIGHT_THRESHOLDS = [(453.592, 'lb'), (0, 'oz')]


def identify_unit_type(unit):
    """Identify whether a unit is volume, weight, or unknown."""
    if not unit:
        return None
    unit_lower = unit.lower().strip()
    if unit_lower in VOLUME_TO_ML:
        return 'volume'
    if unit_lower in WEIGHT_TO_G:
        return 'weight'
    return None


def convert_unit(value, from_unit, to_unit):
    """Convert a value from one unit to another."""
    if not value or not from_unit or not to_unit:
        return None, None

    from_lower = from_unit.lower().strip()
    to_lower = to_unit.lower().strip()

    # Same unit
    if from_lower == to_lower:
        return value, to_unit

    # Volume conversion
    if from_lower in VOLUME_TO_ML and to_lower in VOLUME_TO_ML:
        ml = value * VOLUME_TO_ML[from_lower]
        result = ml / VOLUME_TO_ML[to_lower]
        return round(result, 3), to_unit

    # Weight conversion
    if from_lower in WEIGHT_TO_G and to_lower in WEIGHT_TO_G:
        g = value * WEIGHT_TO_G[from_lower]
        result = g / WEIGHT_TO_G[to_lower]
        return round(result, 3), to_unit

    return None, None


def convert_to_system(value, unit, target_system):
    """Convert a value to the best unit in the target system (metric/imperial)."""
    if not value or not unit:
        return value, unit

    unit_lower = unit.lower().strip()
    unit_type = identify_unit_type(unit_lower)

    if unit_type == 'volume':
        base_ml = value * VOLUME_TO_ML[unit_lower]
        if target_system == 'metric':
            thresholds = METRIC_VOLUME_THRESHOLDS
        else:
            thresholds = IMPERIAL_VOLUME_THRESHOLDS

        for threshold, target_unit in thresholds:
            if base_ml >= threshold:
                result = base_ml / VOLUME_TO_ML[target_unit]
                return round(result, 2), target_unit

    elif unit_type == 'weight':
        base_g = value * WEIGHT_TO_G[unit_lower]
        if target_system == 'metric':
            thresholds = METRIC_WEIGHT_THRESHOLDS
        else:
            thresholds = IMPERIAL_WEIGHT_THRESHOLDS

        for threshold, target_unit in thresholds:
            if base_g >= threshold:
                result = base_g / WEIGHT_TO_G[target_unit]
                return round(result, 2), target_unit

    # Unrecognized unit or no conversion needed
    return value, unit


def convert_temperature(value, from_unit, to_unit):
    """Convert temperature between Fahrenheit and Celsius."""
    from_lower = from_unit.lower().strip()
    to_lower = to_unit.lower().strip()

    if from_lower in ('f', '°f', 'fahrenheit') and to_lower in ('c', '°c', 'celsius'):
        return round((value - 32) * 5 / 9, 1)
    elif from_lower in ('c', '°c', 'celsius') and to_lower in ('f', '°f', 'fahrenheit'):
        return round(value * 9 / 5 + 32, 1)
    return value


def scale_quantity(quantity, original_servings, target_servings):
    """Scale a quantity based on servings ratio."""
    if not quantity or not original_servings or not target_servings:
        return quantity
    if original_servings == 0:
        return quantity
    ratio = target_servings / original_servings
    result = quantity * ratio
    return round(result, 3)


def format_quantity(quantity):
    """Format a quantity for display, using fractions where appropriate."""
    if quantity is None:
        return ''
    if quantity == int(quantity):
        return str(int(quantity))

    # Common fractions
    fractions = {
        0.25: '¼', 0.33: '⅓', 0.5: '½', 0.67: '⅔', 0.75: '¾',
        0.125: '⅛', 0.375: '⅜', 0.625: '⅝', 0.875: '⅞',
    }

    whole = int(quantity)
    frac = round(quantity - whole, 3)

    # Check for common fraction match
    for val, symbol in fractions.items():
        if abs(frac - val) < 0.02:
            if whole > 0:
                return f"{whole} {symbol}"
            return symbol

    # Fall back to decimal
    if quantity == round(quantity, 1):
        return f"{quantity:.1f}"
    return f"{quantity:.2f}"
