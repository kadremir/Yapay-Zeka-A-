import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import subprocess
import requests
import json
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class QuestionGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Model Tabanlı Soru Üretici - Upgraded by Kadir Emirhan Tufan")
        self.root.geometry("700x750")  # Yüksekliği biraz artırdık

        # Model Seçimi Bölümü
        model_frame = ttk.LabelFrame(root, text="Modeller")
        model_frame.pack(fill="x", padx=10, pady=5)

        self.models = self.get_models()
        self.selected_model = tk.StringVar()
        if self.models:
            self.selected_model.set(self.models[0])
        else:
            self.selected_model.set("Model bulunamadı")

        self.model_dropdown = ttk.OptionMenu(model_frame, self.selected_model, *self.models)
        self.model_dropdown.pack(padx=10, pady=10)

        # Alan Seçimi Bölümü
        field_frame = ttk.LabelFrame(root, text="Field Selection")
        field_frame.pack(fill="x", padx=10, pady=5)

        self.selected_field = tk.StringVar()
        fields = ["IT Expertise", "Data Analysis", "Cybersecurity", "Cloud Computing", "Python Programming"]
        self.selected_field.set(fields[0])

        field_dropdown = ttk.OptionMenu(field_frame, self.selected_field, *fields)
        field_dropdown.pack(padx=10, pady=10)

        # Soru Sayısı Seçimi
        question_count_frame = ttk.LabelFrame(root, text="Number of Questions")
        question_count_frame.pack(fill="x", padx=10, pady=5)

        self.question_count = tk.StringVar(value="5")
        question_counts = ["5", "10", "20", "Unlimited"]
        
        for count in question_counts:
            ttk.Radiobutton(question_count_frame, 
                            text=count, 
                            variable=self.question_count, 
                            value=count).pack(side="left", padx=10, pady=5)

        # Soru Üretme Butonu
        self.generate_button = ttk.Button(root, text="Generate Questions", command=self.start_generation)
        self.generate_button.pack(pady=10)

        # Soru Durdurma Butonu
        self.stop_button = ttk.Button(root, text="Stop Generation", command=self.stop_generation, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        # PDF'e Aktarma Butonu
        export_button = ttk.Button(root, text="Export to PDF", command=self.export_to_pdf)
        export_button.pack(pady=10)

        # Yükleme Çubuğu ve Süre
        progress_frame = ttk.Frame(root)
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate')
        self.progress.pack(fill="x", padx=10, pady=5)

        self.time_label = ttk.Label(progress_frame, text="Elapsed Time: 0s")
        self.time_label.pack(pady=5)

        # Çıktı Metin Kutusu
        output_frame = ttk.LabelFrame(root, text="Generated Questions")
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.output_text = tk.Text(output_frame, wrap="word")
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)

        # İmza
        signature_label = ttk.Label(root, text="Upgraded by Kadir Emirhan Tufan", 
                                    font=("Arial", 12, "bold"),
                                    foreground="#4a4a4a")
        signature_label.pack(side="right", padx=10, pady=10)

        self.questions = []
        self.is_generating = False
        self.generation_thread = None

        # Özel stil oluşturma
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10, "bold"))

    def get_models(self):
        try:
            print("Modeller alınyor...")  # Log
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            models = self.parse_ollama_list(result.stdout)
            print(f"Bulunan modeller: {models}")  # Log
            return models if models else ["Model bulunamadı"]
        except Exception as e:
            print(f"Model listesi alınırken hata oluştu: {e}")  # Log
            return ["Model bulunamadı"]

    def parse_ollama_list(self, output):
        models = []
        for line in output.split('\n')[1:]:  # İlk satırı (başlık) atla
            if line.strip():
                model_name = line.split()[0]  # İlk sütun model adı
                models.append(model_name)
        return models

    def start_generation(self):
        if not self.models or self.models[0] == "Model bulunamadı":
            messagebox.showwarning("Uyarı", "Hiç model bulunamadı.")
            return

        selected_model = self.selected_model.get()
        selected_field = self.selected_field.get()

        print(f"Seçilen model: {selected_model}")  # Log
        print(f"Seçilen alan: {selected_field}")  # Log

        self.progress.config(mode='indeterminate')
        self.progress.start()
        self.time_label.config(text="Sorular üretiliyor...")
        self.output_text.delete(1.0, tk.END)
        self.questions = []
        self.is_generating = True

        self.generate_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Soru üretme işlemini ayrı bir thread'de başlat
        self.generation_thread = threading.Thread(target=self.generate_questions, args=(selected_model, selected_field), daemon=True)
        self.generation_thread.start()

    def stop_generation(self):
        self.is_generating = False
        if self.generation_thread and self.generation_thread.is_alive():
            self.generation_thread.join(timeout=1)  # Thread'in durmasın bekle
        self.update_gui(int(time.time() - self.start_time))
        self.generate_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def generate_questions(self, model, field):
        self.start_time = time.time()

        try:
            print("Soru üretme işlemi başladı...")  # Log
            self.questions = self.create_questions_with_ollama(model, field)

            if self.is_generating:
                elapsed = int(time.time() - self.start_time)
                print(f"Soru üretimi tamamlandı. Geçen süre: {elapsed}s")  # Log
                self.root.after(0, self.update_gui, elapsed)
            else:
                print("Soru üretimi kullanıcı tarafından durduruldu.")

        except Exception as e:
            error_message = f"Soru üretme sırasında bir hata oluştu:\n{e}"
            print(error_message)  # Log
            self.root.after(0, self.show_error, error_message)

    def update_gui(self, elapsed):
        self.progress.config(mode='indeterminate')
        self.progress.start()
        self.time_label.config(text=f"Geçen Süre: {elapsed}s")

        self.output_text.delete(1.0, tk.END)  # Önceki içeriği temizle
        if self.questions:
            for q in self.questions:
                self.output_text.insert(tk.END, f"{q}\n\n")
        else:
            self.output_text.insert(tk.END, "Henüz soru üretilmedi.")

        self.output_text.see(tk.END)  # Scroll to the bottom
        self.root.update_idletasks()  # GUI'yi zorla güncelle

        if not self.is_generating:
            self.progress.stop()
            self.progress.config(mode='determinate', value=100)
            self.generate_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def show_error(self, message):
        self.progress.stop()
        self.progress.config(mode='determinate', value=0)
        self.time_label.config(text="Hata oluştu")
        messagebox.showerror("Hata", message)

    def create_questions_with_ollama(self, model, field):
        api_url = "http://localhost:11434/api/generate"
        print(f"API call is being made: {api_url}")  # Log

        question_count = self.question_count.get()
        if question_count == "Unlimited":
            max_questions = float('inf')  # Infinite
        else:
            max_questions = int(question_count)

        prompt = f"Please generate questions in the field of {field}. Number each question. Questions should be in the form of short paragraphs or long sentences. Do not include multiple choice options. Write all questions in English."
        if max_questions != float('inf'):
            prompt += f" Generate a total of {max_questions} questions."

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            with requests.post(api_url, headers=headers, json=payload, stream=True) as response:
                if response.status_code != 200:
                    raise Exception(f"API call failed. Status Code: {response.status_code}, Message: {response.text}")

                full_response = ""
                for line in response.iter_lines():
                    if self.is_generating:
                        if line:
                            try:
                                json_obj = json.loads(line.decode('utf-8'))
                                chunk = json_obj.get("response", "")
                                full_response += chunk
                                print(chunk, end='', flush=True)  # Print each chunk immediately
                                
                                # Update GUI with each new character
                                self.questions = self.extract_questions(full_response)
                                elapsed = int(time.time() - self.start_time)
                                self.root.after(0, self.update_gui, elapsed)

                                # Stop if the specified number of questions has been reached
                                if len(self.questions) >= max_questions:
                                    self.is_generating = False
                                    break
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e}")
                                continue
                    else:
                        break  # User stopped the generation

            print("\nQuestion generation completed.")
            return self.questions

        except requests.exceptions.RequestException as e:
            print(f"API call error: {e}")  # Log
            raise Exception(f"An error occurred during the API call: {e}")
        except Exception as e:
            print(f"General error: {e}")  # Log
            raise Exception(f"An error occurred while processing the response: {e}")

    def extract_questions(self, text):
        pattern = r'(\d+\..*?)(?=\d+\.|$)'
        questions = re.findall(pattern, text, re.DOTALL)
        questions = [q.strip() for q in questions if q.strip()]
        return questions[:5] if len(questions) >= 5 else questions

    def export_to_pdf(self):
        questions = self.output_text.get("1.0", tk.END).strip()
        if not questions:
            messagebox.showwarning("Uyarı", "Aktarılacak soru bulunamadı.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return  # Kullanıcı iptal ettiyse işlemi sonlandır

        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica", 12)
        y = height - 50
        for line in questions.split('\n'):
            if y < 50:
                c.showPage()
                y = height - 50
            c.drawString(50, y, line)
            y -= 20

        c.save()
        messagebox.showinfo("Bilgi", f"Sorular başarıyla {file_path} dosyasına aktarıldı.")

if __name__ == "__main__":
    root = tk.Tk()
    app = QuestionGeneratorApp(root)
    root.mainloop()
