import customtkinter as ctk
import requests
import bs4
import webbrowser
from PIL import Image
import io

ctk.FontManager.load_font("Rajdhani-Bold.ttf")
ctk.FontManager.load_font("Rajdhani-Medium.ttf")
# Setup de CustomTKinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("1000x700")
app.title("Arknights Operator Database V0.0")

app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=3)
app.grid_rowconfigure(1, weight=1)

# Interfaz
var_nombre = ctk.StringVar(value="Search for any EN released Operator...")
var_rarity = ctk.StringVar(value="---")
var_datos = ctk.StringVar(value="Waiting for search...")

# Abrir link de las imágenes
def abrir_chrome_seguro(url):
    if not url: return

    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://arknights.wiki.gg" + url
    print(f"Opening: {url}")
    webbrowser.open(url)

# Ponemos la imagen en el espacio indicado
def cargar_imagen_en_label(url, label_destino):
    if not url: return

    # requests necesita saber que es https, sino falla con los links de la wiki
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://arknights.wiki.gg" + url

    try:
        # 1. Descargar la imagen cruda (bytes)
        response = requests.get(url)
        response.raise_for_status()

        # 2. Convertir bytes a imagen PIL
        image_data = io.BytesIO(response.content)
        pil_image = Image.open(image_data)

        # 3. Calcular tamaño para que entre en la ventana
        ratio = 400 / float(pil_image.size[1])
        nuevo_ancho = int(float(pil_image.size[0]) * float(ratio))

        # 4. Crear objeto CTkImage
        my_image = ctk.CTkImage(light_image=pil_image,
                                dark_image=pil_image,
                                size=(nuevo_ancho, 400))

        # 5. Ponerla en el Label
        label_destino.configure(image=my_image, text="")
        label_destino.image = my_image  # Mantener referencia

    except Exception as e:
        print(f"Error cargando imagen: {e}")
        label_destino.configure(text="Image Error")

# Proceso de búsqueda
def realizar_busqueda():
    operator_buscado = entry_busqueda.get().strip().lower()

    if not operator_buscado:
        return

    var_datos.set("Connecting to the neural network of Rhodes Island...")
    print(f"Buscando a: {operator_buscado}...")
    app.update()

    # Obtenemos el link que lleva a la página del Operator que seleccionamos
    try:
        url_base = "https://arknights.wiki.gg/wiki/Operator/List"
        resultado = requests.get(url_base)
        sopa = bs4.BeautifulSoup(resultado.text, "lxml")

        url_operator = None
        nombre_real = "Unknown"
        encontrado = False

        tablas = sopa.find_all("table")
        tabla_operators = tablas[0]
        filas = tabla_operators.find_all("tr")

        for fila in filas:
            columnas = fila.find_all("td")
            if not columnas: continue

            nombre_tag = columnas[1].find("a")
            nombre_operator_tabla = nombre_tag.text.strip().lower()

            if operator_buscado == nombre_operator_tabla:
                nombre_real = nombre_tag.text.strip()
                print(f"Operator found! ➡️ {nombre_real}")
                link = nombre_tag.get("href")
                url_operator = "https://arknights.wiki.gg" + link
                encontrado = True
                break

        if not encontrado:
            print("Not found")
            var_nombre.set("Not Found")
            var_datos.set(f"Operator '{operator_buscado}' was not found ❌.\nDid you type it correctly?")
            return

        # Obtenemos los datos
        resultado2 = requests.get(url_operator)
        sopa2 = bs4.BeautifulSoup(resultado2.text, "lxml")

        # Rareza
        rareza = "Unknown"
        for texto in sopa2.stripped_strings:
            if "★" in texto:
                rareza = f"{texto.count('★')}⭐"
                break

        # Stats
        tabla_infobox = None
        for tabla in sopa2.find_all("table"):
            texto_tabla = tabla.get_text()
            if "Faction" in texto_tabla and "Class" in texto_tabla:
                tabla_infobox = tabla
                break
        scope_busqueda = tabla_infobox if tabla_infobox else sopa2

        def stats(stat):
            label_text = scope_busqueda.find(string=lambda text: text and stat in text)
            if label_text:
                header_cell = label_text.find_parent(["th", "td"])
                if header_cell:
                    value_cell = header_cell.find_next_sibling("td")
                    if value_cell:
                        dato_limpio = value_cell.get_text(separator=", ", strip=True)
                        if dato_limpio.startswith(stat):
                            dato_limpio = dato_limpio.replace(stat, "", 1).strip(" ,")
                        return dato_limpio
            return "??"

        op_class = stats("Class")
        op_branch = stats("Branch")
        op_faction = stats("Faction")
        op_position = stats("Position")
        op_tags = stats("Tags")
        op_obtain = stats("How to obtain")

        # Mostramos los datos obtenidos en la ventana (texto_completo)
        var_nombre.set(nombre_real)
        var_rarity.set(rareza)

        texto_completo = (
            f"Class: {op_class}\n"
            f"Branch: {op_branch}\n"
            f"Faction: {op_faction}\n"
            f"Position: {op_position}\n"
            f"Tags: {op_tags}\n\n"
            f"Obtain: {op_obtain}"
        )
        var_datos.set(texto_completo)

# Encontrar la introducción del Operator
        scrap_infobox = sopa2.find_all("div", style=True)
        partes_intro = []
        intro_texto = "No quote found."

        for div in scrap_infobox:
            estilo = div['style'].replace(" ", "").lower()
            if "padding:01em" in estilo:
                txt = div.get_text(separator=" ", strip=True)
                txt = " ".join(txt.split())  # Limpiar espacios
                if len(txt) > 5:
                    partes_intro.append(txt)

        if partes_intro:
            intro_texto = "\n\n".join(partes_intro)
        else:
            intro_texto = "No quote found."

            # Actualizamos la caja de texto
        txt_intro.configure(state="normal")
        txt_intro.delete("0.0", "end")

        # Usamos el tag "center" que definiremos abajo
        txt_intro.insert("0.0", f'"{intro_texto}"', "center")

        txt_intro.configure(state="disabled")

        # Actualizamos la caja de texto del Panel Izquierdo
        txt_intro.configure(state="normal")  # Desbloquear
        txt_intro.delete("0.0", "end")  # Borrar anterior
        txt_intro.insert("0.0", f'"{intro_texto}"')  # Escribir nuevo
        txt_intro.configure(state="disabled")  # Bloquear de nuevo

        # Buscamos las imágenes
        img_base_tag = sopa2.select_one(f'img[alt="{nombre_real}.png"]')
        img_e2_tag = sopa2.select_one(f'img[alt="{nombre_real} Elite 2.png"]')

        url_base = None
        url_e2 = None

        if img_base_tag:
            url_base = img_base_tag.get("src")
            # Cargar imagen inicial
            lbl_img_placeholder.configure(text="Loading...", image=None)
            app.update()
            cargar_imagen_en_label(url_base, lbl_img_placeholder)

            # Botón Base
            btn_base.configure(state="normal", command=lambda: cargar_imagen_en_label(url_base, lbl_img_placeholder))
        else:
            btn_base.configure(state="disabled")

        if img_e2_tag:
            url_e2 = img_e2_tag.get("src")
            # Botón E2
            btn_e2.configure(state="normal", command=lambda: cargar_imagen_en_label(url_e2, lbl_img_placeholder))
        else:
            btn_e2.configure(state="disabled")

    except Exception as e:
        print(f"Error: {e}")
        var_datos.set(f"Error: {e}. Try again in a few minutes. ")

# Configuración de la ventana
frame_top = ctk.CTkFrame(app, height=60)
frame_top.grid(row=0, column=0, columnspan=2, sticky="ew")

entry_busqueda = ctk.CTkEntry(frame_top, placeholder_text="Type here...", width=300)
entry_busqueda.pack(side="left", padx=20, pady=15)
entry_busqueda.bind('<Return>', lambda e: realizar_busqueda())

btn_buscar = ctk.CTkButton(frame_top, text="SEARCH", command=realizar_busqueda, font=("Rajdhani", 20))
btn_buscar.pack(side="left")

    # Panel Izquierdo
frame_left = ctk.CTkFrame(app)
frame_left.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

lbl_img_placeholder = ctk.CTkLabel(frame_left, text="[ ARTWORK ]", fg_color="#1a1a1a", height=300, font=("Rajdhani", 11))

lbl_img_placeholder.pack(fill="x", pady=10)

btn_base = ctk.CTkButton(frame_left, text="BASE ART", state="disabled", font=("Rajdhani", 18))
btn_base.pack(pady=5)
btn_e2 = ctk.CTkButton(frame_left, text="ELITE 2", state="disabled", fg_color="#D63031", font=("Rajdhani", 18))
btn_e2.pack(pady=5)

    # Panel Derecho
frame_right = ctk.CTkFrame(app, fg_color="transparent")
frame_right.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)

ctk.CTkLabel(frame_right, textvariable=var_nombre, font=("Rajdhani", 40, "bold"), anchor="w").pack(fill="x")
ctk.CTkLabel(frame_right, textvariable=var_rarity, font=("Rajdhani", 20), text_color="yellow", anchor="w").pack(fill="x")
ctk.CTkFrame(frame_right, height=2, fg_color="gray").pack(fill="x", pady=15)
ctk.CTkLabel(frame_right, textvariable=var_datos, font=("Rajdhani", 18), justify="left", anchor="w").pack(fill="x")
ctk.CTkLabel(frame_right, text="All data shown here comes from https://arknights.wiki.gg/", font=("Rajdhani", 18), text_color="gray", justify="left", anchor="w").pack(fill="x")

    # Operator Intro
ctk.CTkLabel(frame_left, text="OPERATOR QUOTE:", font=("Rajdhani", 20, "bold"),text_color="#AFAFAF").pack(fill="x", pady=(20, 0))

txt_intro = ctk.CTkTextbox(frame_left, height=120, font=("Rajdhani", 16), fg_color="#2B2B2B", text_color="#E0E0E0", wrap="word")
txt_intro.pack(fill="both", expand=True, pady=10)

txt_intro.tag_config("center", justify='center')

txt_intro.insert("0.0", "...", "center")
txt_intro.configure(state="disabled")
app.mainloop()