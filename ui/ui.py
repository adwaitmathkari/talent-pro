import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests
import os
import json

# Dummy users database
users = {
    "e": {"password": "e", "role": "employee"},
    "m": {"password": "m", "role": "manager"}
}

API_URL = "http://127.0.0.1:5000/upload"  # <== REPLACE this with your actual API endpoint
CHAT_API_URL = 'http://127.0.0.1:5000/search?query="'  # <-- Replace with your real chatbot API URL


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

uploaded_pdf_path = None

def upload_pdf():
    global uploaded_pdf_path
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        uploaded_pdf_path = file_path
        pdf_label.configure(text=f"Selected: {os.path.basename(file_path)}")

def send_resume_to_api(github_url, pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            files = {'file': (os.path.basename(pdf_path), file, 'application/pdf')}
            data = {'github_url': github_url}

            response = requests.post(API_URL, files=files, data=data)
            return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def submit_employee_details():
    github_url = github_entry.get()

    if not uploaded_pdf_path:
        messagebox.showwarning("Missing PDF", "Please upload your resume PDF.")
        return

    status, result = send_resume_to_api(github_url, uploaded_pdf_path)

    # Open a new screen to show result and back button
    result_window = ctk.CTkToplevel()
    result_window.geometry("500x400")
    result_window.title("Submission Result")

    # Response Message
    if status == 200:
        message = f"✅ Success:\n{result}"
        color = "green"
    else:
        message = f"❌ Error {status}:\n{result}"
        color = "red"

    ctk.CTkLabel(result_window, text=message, text_color=color, wraplength=450, justify="left").pack(pady=30, padx=20)

    # 🔙 Back Button
    def go_back():
        result_window.destroy()  # Close result window
        open_employee_page()     # Reopen upload screen

    ctk.CTkButton(result_window, text="Back", command=go_back).pack(pady=20)

# Employee Page
def open_employee_page():
    emp_window = ctk.CTkToplevel()
    emp_window.geometry("500x450")
    emp_window.title("Employee Dashboard")
    global response_label
    response_label = ctk.CTkLabel(emp_window, text="", justify="left", wraplength=450)
    response_label.pack(pady=15, padx=10)

    # ctk.CTkLabel(emp_window, text="Welcome Employee 👷", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)

    ctk.CTkButton(emp_window, text="Upload Resume (PDF)", command=upload_pdf).pack(pady=5)
    global pdf_label
    pdf_label = ctk.CTkLabel(emp_window, text="No PDF selected", text_color="gray")
    pdf_label.pack(pady=5)

    ctk.CTkLabel(emp_window, text="GitHub URL:", anchor="w").pack(pady=(20, 5), fill="x", padx=50)
    global github_entry
    github_entry = ctk.CTkEntry(emp_window, placeholder_text="https://github.com/username")
    github_entry.pack(padx=50, pady=5, ipadx=5, ipady=5, fill="x")

    ctk.CTkButton(emp_window, text="Submit", command=submit_employee_details).pack(pady=20)

def open_manager_page():
    mgr_window = ctk.CTkToplevel()
    mgr_window.geometry("500x600")
    mgr_window.title("Manager Dashboard")

    ctk.CTkLabel(mgr_window, text="Manager Chatbot 🤖", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

    # Chat Display
    global chat_display
    chat_display = ctk.CTkTextbox(mgr_window, height=400, state="disabled", wrap="word")
    chat_display.pack(padx=20, pady=10, fill="both", expand=True)

    # Entry & Button
    input_frame = ctk.CTkFrame(mgr_window)
    input_frame.pack(padx=20, pady=10, fill="x")

    global chat_entry
    chat_entry = ctk.CTkEntry(input_frame, placeholder_text="Type your message...")
    chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

    send_button = ctk.CTkButton(input_frame, text="Send", command=send_message)
    send_button.pack(side="right")


def send_message():
    user_msg = chat_entry.get().strip()
    if user_msg:
        update_chat("You", user_msg)
        chat_entry.delete(0, "end")
        mgr_response = get_bot_response(user_msg)
        update_chat("Bot", mgr_response)

def update_chat(sender, message):
    chat_display.configure(state="normal")
    if sender == "You":
        chat_display.insert("end", f"👤 {sender}:\n{message}\n\n", "user")
    else:
        chat_display.insert("end", f"🤖 {sender}:\n{message}\n\n", "bot")
    chat_display.tag_config("user", foreground="#00bfff")
    chat_display.tag_config("bot", foreground="#22c55e")
    chat_display.configure(state="disabled")
    chat_display.see("end")

def get_bot_response(message):
    try:
        print('search::',CHAT_API_URL+message+'"')
        response = requests.get(CHAT_API_URL+message+'"')
        print("response::",response.text)
        # if response.status_code == 200:
        #     return response.json().get("reply", "No reply received.")
        # else:
        #     return f"Error {response.status_code}: {response.text}"

        data = response.json().get("results", {})
        if isinstance(data, (dict, list)):
            return json.dumps(data, indent=4)  # 👈 Pretty print with tabs/spaces
        return str(data)  # If 'results' is a simple string
        # return response.json().get("results")
    except Exception as e:
        return f"❗ Error contacting API: {e}"



def login():
    username = username_entry.get()
    password = password_entry.get()

    user = users.get(username)
    if user and user["password"] == password:
        # messagebox.showinfo("Login Success", f"Welcome {username}!")
        app.destroy()
        if user["role"] == "employee":
            open_employee_page()
        elif user["role"] == "manager":
            open_manager_page()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password!")

# Main Window Setup
app = ctk.CTk()
app.geometry("400x350")
app.title("Company Login Portal")

ctk.CTkLabel(app, text="Login to Dashboard", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

username_entry = ctk.CTkEntry(app, placeholder_text="Username")
username_entry.pack(pady=10, ipadx=5, ipady=5)

password_entry = ctk.CTkEntry(app, placeholder_text="Password", show="*")
password_entry.pack(pady=10, ipadx=5, ipady=5)

ctk.CTkButton(app, text="Login", command=login, width=150).pack(pady=25)

ctk.CTkLabel(app, text="© 2025 YourCompany", font=ctk.CTkFont(size=10)).pack(side="bottom", pady=10)

app.mainloop()
