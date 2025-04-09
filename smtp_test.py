import smtplib

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("tdsparis15@gmail.com", "wkah dsma cotv stga")  # ← ou ton mot de passe d’application

        subject = "Test Gmail SSL"
        body = "Ceci est un test envoyé via Gmail SMTP."
        message = f"Subject: {subject}\n\n{body}".encode("utf-8")  # 👈 encodage ici

        server.sendmail("tdsparis15@gmail.com", "lionelboukris@gmail.com", message)
        print("✅ Email envoyé avec succès via Gmail !")

except Exception as e:
    print(f"❌ Erreur : {e}")