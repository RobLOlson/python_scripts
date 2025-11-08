import math
import random

_ELEMENT_SYMBOL_TO_NAME_AND_ATOMIC_NUMBER = {
    "H": ("hydrogen", 1),
    "He": ("helium", 2),
    "Li": ("lithium", 3),
    "Be": ("beryllium", 4),
    "B": ("boron", 5),
    "C": ("carbon", 6),
    "N": ("nitrogen", 7),
    "O": ("oxygen", 8),
    "F": ("fluorine", 9),
    "Ne": ("neon", 10),
    "Na": ("sodium", 11),
    "Mg": ("magnesium", 12),
    "Al": ("aluminum", 13),
    "Si": ("silicon", 14),
    "P": ("phosphorus", 15),
    "S": ("sulfur", 16),
    "Cl": ("chlorine", 17),
    "Ar": ("argon", 18),
    "K": ("potassium", 19),
    "Ca": ("calcium", 20),
    "Sc": ("scandium", 21),
    "Ti": ("titanium", 22),
    "V": ("vanadium", 23),
    "Cr": ("chromium", 24),
    "Mn": ("manganese", 25),
    "Fe": ("iron", 26),
    "Co": ("cobalt", 27),
    "Ni": ("nickel", 28),
    "Cu": ("copper", 29),
    "Zn": ("zinc", 30),
    "Ga": ("gallium", 31),
    "Ge": ("germanium", 32),
    "As": ("arsenic", 33),
    "Se": ("selenium", 34),
    "Br": ("bromine", 35),
    "Kr": ("krypton", 36),
}

_ELEMENT_NAME_TO_SYMBOL = {value[0]: key for key, value in _ELEMENT_SYMBOL_TO_NAME_AND_ATOMIC_NUMBER.items()}

_ELEMENT_SYMBOL_TO_NAME = {key: value[0] for key, value in _ELEMENT_SYMBOL_TO_NAME_AND_ATOMIC_NUMBER.items()}

_ELEMENT_NAMES = list(_ELEMENT_NAME_TO_SYMBOL.keys())
_ELEMENT_SYMBOLS = list(_ELEMENT_SYMBOL_TO_NAME.keys())


def generate_water_formula(freq_weight: int = 1000, difficulty: int | None = None) -> tuple[str, str]:
    """Generate a basic chemical formula identification problem.
    Problem Description:
    Chemical Formula Identification"""

    problem = "What is the chemical formula for water?"
    solution = "H$_2$O"
    return (problem, solution)


def generate_elementary_chemical_formula(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate an elementary chemical formula identification problem.
    Problem Description:
    Chemical Formula Identification"""
    import random

    # Basic, commonly known compounds with LaTeX-friendly subscripts
    # Keep to "elementary"/intro level recognitions
    name_to_formula = {
        "water": "H$_2$O",
        "oxygen gas": "O$_2$",
        "hydrogen gas": "H$_2$",
        "nitrogen gas": "N$_2$",
        "carbon dioxide": "CO$_2$",
        "carbon monoxide": "CO",
        "methane": "CH$_4$",
        "ammonia": "NH$_3$",
        "ozone": "O$_3$",
        "sodium chloride (table salt)": "NaCl",
        "hydrochloric acid": "HCl",
        "sulfuric acid": "H$_2$SO$_4$",
        "sodium bicarbonate (baking soda)": "NaHCO$_3$",
        "calcium carbonate": "CaCO$_3$",
        "ethanol": "C$_2$H$_5$OH",
        "glucose": "C$_6$H$_{12}$O$_6$",
    }

    # Optionally scale pool by difficulty (easier omits multi-subscript organics)
    if difficulty is None:
        # Mirror algebra difficulty pattern lightly without heavy dependency
        try:
            import math

            difficulty = int(3 - math.log(freq_weight + 1, 10))
        except Exception:
            difficulty = 2

    if difficulty <= 1:
        pool_keys = [
            "water",
            "oxygen gas",
            "hydrogen gas",
            "nitrogen gas",
            "carbon dioxide",
            "carbon monoxide",
            "methane",
            "ammonia",
            "sodium chloride (table salt)",
        ]
    elif difficulty == 2:
        pool_keys = [
            "water",
            "oxygen gas",
            "hydrogen gas",
            "nitrogen gas",
            "carbon dioxide",
            "methane",
            "ammonia",
            "ozone",
            "sodium chloride (table salt)",
            "hydrochloric acid",
            "sodium bicarbonate (baking soda)",
            "calcium carbonate",
        ]
    else:
        pool_keys = list(name_to_formula.keys())

    compound = random.choice(pool_keys)
    problem = f"What is the chemical formula for {compound}?"
    solution = name_to_formula[compound]
    return (problem, solution)


def generate_identify_element_name_problem(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate an element name identification problem.
    Problem Description:
    Element Name Identification"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    if difficulty >= 1:
        element_symbols = ["H", "He", "Li", "N", "O", "C", "F", "P", "K", "B", "S"]
    else:
        element_symbols = _ELEMENT_SYMBOLS
    element_symbol = random.choice(element_symbols)
    element, atomic_number = _ELEMENT_SYMBOL_TO_NAME_AND_ATOMIC_NUMBER[element_symbol]
    problem = f"What is the name of the element with the symbol {element_symbol}?"
    solution = element
    return (problem, solution)


def generate_identify_element_symbol_problem(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate an element symbol identification problem.
    Problem Description:
    Element Symbol Identification"""
    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))
    if difficulty >= 1:
        element_symbols = ["H", "He", "Li", "N", "O", "C", "F", "P", "K", "B"]
    else:
        element_symbols = _ELEMENT_SYMBOLS
    element_symbol = random.choice(element_symbols)
    element, atomic_number = _ELEMENT_SYMBOL_TO_NAME_AND_ATOMIC_NUMBER[element_symbol]
    problem = f"What is the chemical symbol for {element}?"
    solution = element_symbol
    return (problem, solution)


def generate_ion_charge_problem(freq_weight: int = 1000, difficulty: int | None = None) -> tuple[str, str]:
    """Generate an ion charge problem.
    Problem Description:
    Ion Charge Calculation"""
    import random

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    if difficulty >= 1:
        charge = random.choice([-1, 0, 1])
        element_symbols = [
            "Li",
            "K",
            "Ca",
            "F",
            "O",
            "Mg",
            "Na",
        ]
    else:
        charge = random.choice([-2, -1, 0, 1, 2])
        element_symbols = _ELEMENT_SYMBOLS

    element_symbol = random.choice(element_symbols)
    element, atomic_number = _ELEMENT_SYMBOL_TO_NAME_AND_ATOMIC_NUMBER[element_symbol]
    problem = f"A {element} ion has {atomic_number - charge} electrons. What is the charge of the ion? \\\\ BONUS: Is this ion likely to be stable?"
    solution = f"{charge}"
    return (problem, solution)


def generate_electron_count_problem(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate an electron count problem.
    Problem Description:
    Electron Count Calculation"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    if difficulty >= 1:
        charge = random.choice([-1, 0, 1])
        element_symbols = [
            "Li",
            "K",
            "Ca",
            "F",
            "O",
            "Mg",
            "Na",
        ]
    else:
        charge = random.choice([-2, -1, 0, 1, 2])
        element_symbols = _ELEMENT_SYMBOLS

    element_symbol = random.choice(element_symbols)
    element, atomic_number = _ELEMENT_SYMBOL_TO_NAME_AND_ATOMIC_NUMBER[element_symbol]
    problem = f"A {element} ion has a net charge of {charge}. How many electrons does it have?"

    solution = f"{atomic_number - charge}"
    return (problem, solution)


def generate_isotope_notation_problem(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate an isotope-notation identification problem.
    Problem Description:
    Isotope Notation Parts"""

    # Choose a fairly common-period element to keep notation familiar
    element_symbol = random.choice(_ELEMENT_SYMBOLS)
    element_name, atomic_number = _ELEMENT_SYMBOL_TO_NAME_AND_ATOMIC_NUMBER[element_symbol]

    # Pick a plausible mass number near ~2×Z, ensure A > Z
    base = max(atomic_number * 2 + random.randint(-2, 3), atomic_number + 1)
    mass_number = base

    # LaTeX-style isotope notation
    notation = f"$^{{{mass_number}}}_{{{atomic_number}}}\\mathrm{{{element_symbol}}}$"

    problem = (
        "The notation for an isotope of "
        f"{element_name} is shown below.\n\n"
        f"{notation}\n\n"
        "How many protons are in this isotope? How many neutrons?"
    )

    solution = f"{atomic_number} protons, {mass_number - atomic_number} neutrons"

    return (problem, solution)


def generate_valence_electron_count_problem(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate a valence-electron counting problem for a neutral atom.
    Problem Description:
    Valence Electron Count"""

    # Map a small, classroom-friendly set of symbols to valence electrons
    # (main-group convention). Helium is a special case with 2.
    symbol_to_valence: dict[str, int] = {
        "H": 1,
        "He": 2,
        "Li": 1,
        "Be": 2,
        "B": 3,
        "C": 4,
        "N": 5,
        "O": 6,
        "F": 7,
        "Ne": 8,
        "Na": 1,
        "Mg": 2,
        "Al": 3,
        "Si": 4,
        "P": 5,
        "S": 6,
        "Cl": 7,
        "Ar": 8,
        "K": 1,
        "Ca": 2,
    }

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    # Progressively widen the pool with difficulty
    easy_pool = ["Li", "Be", "B", "C", "N", "O", "F", "Na", "Mg", "Al", "Si", "P", "S", "Cl"]
    medium_pool = list(symbol_to_valence.keys())

    if difficulty > 1:
        candidate_symbols = easy_pool
    else:
        candidate_symbols = medium_pool

    symbol = random.choice(candidate_symbols)
    valence = symbol_to_valence[symbol]

    # Prefer concise statement mirroring worksheet-style phrasing
    problem = f"How many valence electrons does a neutral {symbol} atom have?"
    solution = f"{valence}"
    return (problem, solution)
