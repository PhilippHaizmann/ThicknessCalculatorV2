import math
import numpy as np
from tkinter import messagebox, Tk, StringVar, Label, Entry, Listbox, Scrollbar, OptionMenu, Button
import sqlite3

def initialize_database():
    conn = sqlite3.connect('TC_database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orbital_properties (
        id INTEGER PRIMARY KEY,
        orbital TEXT,
        cross_section REAL,
        energy REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS material_properties (
        id INTEGER PRIMARY KEY,
        material_name TEXT UNIQUE,
        density REAL,
        molar_mass REAL
    )
    ''')

    conn.commit()
    conn.close()

initialize_database()

def populate_with_default_data():
    conn = sqlite3.connect('TC_database.db')
    cursor = conn.cursor()
    
    # Check if the orbital_properties table is empty
    cursor.execute('SELECT COUNT(*) FROM orbital_properties')
    if cursor.fetchone()[0] == 0:
        default_orbitals = [
            ('Mo3d',0.1303,1486.6),
        ]
        cursor.executemany('INSERT INTO orbital_properties(orbital, cross_section, energy) VALUES (?, ?, ?)', default_orbitals)
     # Check if the material_properties table is empty
    cursor.execute('SELECT COUNT(*) FROM material_properties')
    if cursor.fetchone()[0] == 0:
        default_material_properties = [
            ('MoS2', 5.06 ,160.07),
        ]
        cursor.executemany('INSERT INTO material_properties(material_name, density,molar_mass) VALUES (?, ?, ?)', default_material_properties)

    conn.commit()
    conn.close()

populate_with_default_data()

def fetch_all_orbital_properties():
    conn = sqlite3.connect('TC_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT orbital, cross_section, energy FROM orbital_properties")
    data = cursor.fetchall()
    conn.close()
    return {
        "orbitals": [item[0] for item in data],
        "cross_sections": [item[1] for item in data],
        "energy": [item[2] for item in data]
    }

def fetch_all_material_properties():
    conn = sqlite3.connect('TC_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT material_name, density, molar_mass FROM material_properties")
    data = cursor.fetchall()
    conn.close()
    return {
        "material_name": [item[0] for item in data],
        "density": [item[1] for item in data],
        "molar_mass": [item[2] for item in data]
    }

def get_value_from_data(name, category, energy="1486.6"):
    conn = sqlite3.connect('TC_database.db')
    cursor = conn.cursor()

    try:
        if category == "orbitals":
            cursor.execute("SELECT cross_section FROM orbital_properties WHERE orbital = ? AND energy = ?", (name,energy,))
            result = cursor.fetchone()
            if result:
                return result[0]
        elif category == "molar_mass":
            cursor.execute("SELECT molar_mass FROM material_properties WHERE material_name = ?", (name,))
            result = cursor.fetchone()
            if result:
                return result[0]
        elif category == "density":
            cursor.execute("SELECT density FROM material_properties WHERE material_name = ?", (name,))
            result = cursor.fetchone()
            if result:
                return result[0]
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Failed to fetch data from the database. Error: {e}")
        return None
    finally:
        conn.close()

def insert_orbital():
    conn = sqlite3.connect('TC_database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO orbital_properties (orbital, cross_section, energy) VALUES (?, ?, ?)", (orbital_text.get(), float(cross_section_text.get()),float(energy_text.get())))
        conn.commit()
        messagebox.showinfo("Success", "Orbital data added successfully!")
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Failed to add data. Error: {e}")
    finally:
        conn.close()


def insert_material():
    conn = sqlite3.connect('TC_database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO material_properties (material_name, density, molar_mass) VALUES (?, ?, ?)", (material_name_text.get(), float(density_text.get()), float(molar_mass_text.get())))
        conn.commit()
        messagebox.showinfo("Success", "Material data added successfully!")
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Failed to add data. Error: {e}")
    finally:
        conn.close()

def table_exists(table_name):
    conn = sqlite3.connect('TC_database.db')
    cursor = conn.cursor()
    cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? ''', (table_name,))
    if cursor.fetchone()[0] == 1:
        conn.close()
        return True
    conn.close()
    return False

def calculate_thickness():
    try:
        E_kin = float(E_ex_text.get()) - float(E_b_text.get())
        dens_film = get_value_from_data(o_var_density_film.get(), "density")

        if dens_film is None:
            raise ValueError("Invalid film density value.")
        
        mfp = (49 / math.pow(E_kin,2) + 0.11 * math.pow(E_kin,0.5)) / dens_film
        mass_sub = get_value_from_data(o_var_molar_mass_sub.get(), "molar_mass")
        dens_sub = get_value_from_data(o_var_density_sub.get(), "density")
        
        if mass_sub is None or dens_sub is None:
            raise ValueError("Invalid substrate values.")
        
        em_sub = mass_sub / (dens_sub * float(N_i_sub_text.get()))
        em_film = get_value_from_data(o_var_molar_mass_film.get(), "molar_mass") / (dens_film * float(N_i_film_text.get()))
        
        if em_film is None:
            raise ValueError("Invalid film emitter value.")
        
        thickness = mfp * math.cos(float(Angle_text.get())) * math.log(
            1 + (
                (float(I_film_text.get()) * get_value_from_data(o_var_pics_sub.get().split(' @ ')[0], "orbitals",E_ex_text.get()) * em_film) / 
                (float(I_sub_text.get()) * get_value_from_data(o_var_pics_film.get().split(' @ ')[0], "orbitals",E_ex_text.get()) * em_sub)
            )
        )
        
        results = [mfp, 1/em_sub, 1/em_film, thickness]
        names = ["mean free path", "emitter substrate", "emitter film", "layer thickness"]
        
        list1.delete(0, 'end')
        for name, result in zip(names, results):
            list1.insert('end', name)
            list1.insert('end', result)
            
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid Input: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Calculation failed. Error: {e}")



# Loading data from SQLite database
orbital_data = fetch_all_orbital_properties()
material_data = fetch_all_material_properties()

# Merging the two data sources
data = {**orbital_data, **material_data}
print(data)
window = Tk()
window.title("Film Thickness Calculator")

############################### Labels first column ###############
l1=Label(window, text="p Sub [g/cm³]")
l1.grid(row=0,column=0)

l2=Label(window, text="M Sub [g/Mol]")
l2.grid(row=2,column=0)

l4=Label(window, text="Ni Sub")
l4.grid(row=4,column=0)

l12=Label(window, text="Results")
l12.grid(row=10,column=0)
################################### Labels second column #############
l6=Label(window, text="p Film [g/cm³]")
l6.grid(row=0,column=1)

l7=Label(window, text="M Film [g/Mol]")
l7.grid(row=2,column=1)

l9=Label(window, text="Ni Film")
l9.grid(row=4,column=1)

################################### Labels third column #############
l11=Label(window, text="I Sub")
l11.grid(row=0,column=2)

l14=Label(window, text="PICS Sub")
l14.grid(row=2,column=2)

l16=Label(window, text="Excitation energy [eV]")
l16.grid(row=4,column=2)

l18=Label(window, text="Measurement Angle")
l18.grid(row=6,column=2)

################################### Labels fourth column #############
l13=Label(window, text="I Film")
l13.grid(row=0,column=3)

l15=Label(window, text="PICS Film")
l15.grid(row=2,column=3)

l17=Label(window, text="Binding Energy [eV]")
l17.grid(row=4,column=3)
################################### Entry boxes first column #############

N_i_sub_text = StringVar()
e4=Entry(window,textvariable=N_i_sub_text)
e4.grid(row=5,column=0)

################################### Entry boxes second column #############

N_i_film_text = StringVar()
e9=Entry(window,textvariable=N_i_film_text)
e9.grid(row=5,column=1)

################################### Entry boxes third column #############
I_sub_text = StringVar()
e11=Entry(window,textvariable=I_sub_text)
e11.grid(row=1,column=2)

E_ex_text = StringVar()
E_ex_text .set("1486.6")
e13=Entry(window,textvariable=E_ex_text)
e13.grid(row=5,column=2)

Angle_text = StringVar()
Angle_text.set("0")
e15=Entry(window,textvariable=Angle_text)
e15.grid(row=7,column=2)
################################### Entry boxes fourth column #############
I_film_text = StringVar()
e12=Entry(window,textvariable=I_film_text)
e12.grid(row=1,column=3)

E_b_text = StringVar()
e14=Entry(window,textvariable=E_b_text)
e14.grid(row=5,column=3)
################################## List Box ###############
list1=Listbox(window, height=10, width=55)
list1.grid(row=11, column=0, rowspan=4, columnspan=4)

sb1=Scrollbar(window)
sb1.grid(row=11, column=4, rowspan=4)

list1.configure(yscrollcommand=sb1.set)
sb1.configure(command=list1.yview)

################################## Select Box ###############
# Create a mapping from the display string to the underlying data
display_to_data = {
    f"{data['orbitals'][i]} @ {data['energy'][i]} eV": {
        'orbital': data['orbitals'][i],
        'cross_section': data['cross_sections'][i],
        'energy': data['energy'][i],
    }
    for i in range(len(data['orbitals']))
}

default_display_string = f"{data['orbitals'][0]} @ {data['energy'][0]} eV"

o_var_pics_sub = StringVar(window)
o_var_pics_sub.set(default_display_string)

o1_pics_sub = OptionMenu(window, o_var_pics_sub, *display_to_data.keys())
o1_pics_sub.grid(row=3,column=2)

# o_var_pics_sub= StringVar(window)
# o_var_pics_sub.set(data["orbitals"][0])

# o1_pics_sub = OptionMenu(window, o_var_pics_sub, *data["orbitals"])
# o1_pics_sub.grid(row=3,column=2)

o_var_pics_film= StringVar(window)
o_var_pics_film.set(default_display_string)

o2_pics_film = OptionMenu(window, o_var_pics_film, *display_to_data.keys())
o2_pics_film.grid(row=3,column=3)

o_var_density_sub= StringVar(window)
o_var_density_sub.set(data["material_name"][0])

o3_density_sub = OptionMenu(window, o_var_density_sub, *data["material_name"])
o3_density_sub.grid(row=1,column=0)

o_var_molar_mass_sub= StringVar(window)
o_var_molar_mass_sub.set(data["material_name"][0])

o4_molar_mass_sub = OptionMenu(window, o_var_molar_mass_sub, *data["material_name"])
o4_molar_mass_sub.grid(row=3,column=0)

o_var_density_film= StringVar(window)
o_var_density_film.set(data["material_name"][0])

o5_density_film = OptionMenu(window, o_var_density_film, *data["material_name"])
o5_density_film.grid(row=1,column=1)

o_var_molar_mass_film= StringVar(window)
o_var_molar_mass_film.set(data["material_name"][0])

o6_molar_mass_film = OptionMenu(window, o_var_molar_mass_film, *data["material_name"])
o6_molar_mass_film.grid(row=3,column=1)

b1 = Button(window, text="Calculate Thickness", command=calculate_thickness)
b1.grid(row=10, column=2, columnspan=2)

# For orbital_properties table
orbital_label = Label(window, text="Orbital Name:")
orbital_label.grid(row=16, column=0)
orbital_text = StringVar()
orbital_entry = Entry(window, textvariable=orbital_text)
orbital_entry.grid(row=17, column=0)

cross_section_label = Label(window, text="Cross Section:")
cross_section_label.grid(row=16, column=1)
cross_section_text = StringVar()
cross_section_entry = Entry(window, textvariable=cross_section_text)
cross_section_entry.grid(row=17, column=1)

energy_label = Label(window, text="Energy [eV]:")
energy_label.grid(row=16, column=2)
energy_text = StringVar()
energy_entry = Entry(window, textvariable=energy_text)
energy_entry.grid(row=17, column=2)

# For material_properties table
material_name_label = Label(window, text="Material Name:")
material_name_label.grid(row=18, column=0)
material_name_text = StringVar()
material_name_entry = Entry(window, textvariable=material_name_text)
material_name_entry.grid(row=19, column=0)

density_label = Label(window, text="Density [g/cm³]:")
density_label.grid(row=18, column=1)
density_text = StringVar()
density_entry = Entry(window, textvariable=density_text)
density_entry.grid(row=19, column=1)

molar_mass_label = Label(window, text="Molar Mass [g/mol]:")
molar_mass_label.grid(row=18, column=2)
molar_mass_text = StringVar()
molar_mass_entry = Entry(window, textvariable=molar_mass_text)
molar_mass_entry.grid(row=19, column=2)

orbital_button = Button(window, text="Add Orbital Data", command=insert_orbital)
orbital_button.grid(row=17, column=3)

material_button = Button(window, text="Add Material Data", command=insert_material)
material_button.grid(row=21, column=3)


window.mainloop()
