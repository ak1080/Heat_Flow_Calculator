# Dictionary of typical R-values below. The Key is the name and Value is the R-value. User can add more if desired.
materials_r_values = {
    # material_r_values.py
    "1/2-inch Drywall (R=0.45)": 0.45,
    "5/8-inch Drywall (R=0.56)": 0.56,
    "1/2-inch Plywood (R=0.63)": 0.63,
    "3/4-inch Plywood (R=0.94)": 0.94,
    "1/2-inch OSB (R=0.50)": 0.50,
    "3/4-inch Solid Wood (Pine) (R=0.81)": 0.81,
    "1-inch Solid Wood (Pine) (R=1.25)": 1.25,
    "1/2-inch Cement Board (R=0.20)": 0.20,
    "8-inch Concrete Block (unfilled) (R=1.11)": 1.11,
    "8-inch Concrete Block (foam filled) (R=2.00)": 2.00,
    "8-inch Reinforced Concrete (R=1.20)": 1.20,
    "3.5-inch Fiberglass Batt (R=13.00)": 13.00,
    "6-inch Fiberglass Batt (R=19.00)": 19.00,
    "8-inch Fiberglass Batt (R=25.00)": 25.00,
    "8-inch Cellulose (Loose-Fill) (R=24.00)": 24.00,
    "1-inch Extruded Polystyrene (XPS) (R=5.00)": 5.00,
    "2-inch Extruded Polystyrene (XPS) (R=10.00)": 10.00,
    "1-inch Expanded Polystyrene (EPS) (R=4.00)": 4.00,
    "2-inch Expanded Polystyrene (EPS) (R=8.00)": 8.00,
    "1-inch Polyiso Foam Board (R=6.50)": 6.50,
    "2-inch Polyiso Foam Board (R=13.00)": 13.00,
}

if __name__ == "__main__":
    # Example usage
    for material, r_val in materials_r_values.items():
        print(f"{material}: R = {r_val}")
