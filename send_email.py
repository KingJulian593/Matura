import smtplib
from smtplib import SMTPException, SMTPAuthenticationError, SMTPConnectError

def send_email(user_username,user_password,e_mail):
    try:
        # ustvari SMTP objekt in poveži se na strežnik
        smtpObj = smtplib.SMTP('smtp.gmail.com', 587)

        # Identifikacija se strežniku ESMTP z uporabo EHLO
        smtpObj.ehlo()

        # Zavaruj povezavo z uporabo TLS
        smtpObj.starttls()

        # Prijavi se na strežnik
        smtpObj.login('lekarneotocec@gmail.com', 'xvqz shyz nkil jnid')

        #pripravi sporočilo
        from_address = 'lekarneotocec@gmail.com'
        to_address = e_mail

        message = f"""\
        Subject: LOGIN CREDENTIALS

        Username: {user_username}
        Password: {user_password}

        After first login go to profile details and change your password.    

        DO NOT ANSWER,
        Sent from Lekarne Otocec.
        """
        #pošlji sporočilo
        smtpObj.sendmail(from_address, to_address, message)

        print("Succsesfull")

        # prekini povezavo
        smtpObj.quit()

    except SMTPAuthenticationError as e:
        print("Authentication failed:", e)
    except SMTPConnectError as e:
        print("Connection failed:", e)
    except SMTPException as e:
        print("SMTP error occurred:", e)
    except Exception as e:
        print("An unexpected error occurred:", e)

