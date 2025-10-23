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
