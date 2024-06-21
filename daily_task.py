import datetime
import base64
from openai import OpenAI
import shutil
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

### Secrets
# Set your OpenAI API key
client = OpenAI(api_key="{Your OpenAI API Key}")
# Set your email and password
my_email = "{my gmail account}"
password = "{my password}"


def send_email(subject, body):

    # Create the email headers
    msg = MIMEMultipart()
    msg['From'] = my_email
    msg['To'] = my_email
    msg['Subject'] = subject

    # Attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Create a secure SSL context and send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(my_email, password)
        text = msg.as_string()
        server.sendmail(my_email, my_email, text)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def holiday_lookup():
    today = datetime.date.today()

    date_str = today.strftime("%B %d")
    myPrompt = f"Please return a list of at least five national and alternative holidays in the US for only this date {date_str}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
              "role": "system",
              "content": [
                {
                  "type": "text",
                  "text": "I want you to be very direct in your responses.  Please don't give me your helpful friendly responses, and only respond with the text I'm asking for."
                }
              ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": myPrompt
                    }
                ]
            }
        ],
        temperature=0.5,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    holiday_data = response.choices[0].message.content

    return holiday_data

def refine_data_with_chatgpt(data):
    myPrompt= "Out of these possible holidays for today, please recommend the most ridiculous or absurd choice as the theme:\n" + data
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "I want you to be very direct in your responses.  Please don't give me your helpful friendly responses, and only respond with the text I'm asking for."
                    }
                ]
            },
            {"role": "user", "content": myPrompt}],
        temperature = 0.5,
        max_tokens = 256,
        top_p = 1,
        frequency_penalty = 0,
        presence_penalty = 0
    )
    chosenResponse = response.choices[0].message.content
    myPrompt2= "ok, please write the prompt I should send to DALL-E to create a photorealistic image for that holiday, making sure that the image incorporates humans and androids participating in celebrating that holiday. You should pick a suitable background setting for the holiday representing a realistic yet whimsical setting where humans and androids would celebrate. Additionally, the image will have a banner with the name of the holiday, but only if you can spell it correctly."
    response = client.chat.completions.create(
        model="gpt-4o",
        messages = [
            {
              "role": "system",
              "content": [
                {
                  "type": "text",
                  "text": "I want you to be very direct in your responses.  Please don't give me your helpful friendly responses, and only respond with the text I'm asking for."
                }
              ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": myPrompt
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": chosenResponse
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": myPrompt2
                    }
                ]
            }
        ],
        temperature = 1,
        max_tokens = 256,
        top_p = 1,
        frequency_penalty = 0,
        presence_penalty = 0
    )
    raw_data = response.choices[0].message.content

    return raw_data

def generate_image_with_dalle(prompt):
    today = datetime.date.today()
    date_str = today.strftime("%B%d")

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1792x1024",
        quality="hd"
#        ,style="natural" #default "vivid"
        ,response_format="b64_json"
    )
    image_base64_json = response.data[0].b64_json

    image_data = base64.b64decode(image_base64_json)
    base_path = os.getcwd()
    image_path = base_path + f"/background{date_str}.png"
    with open(image_path, 'wb') as image_file:
        image_file.write(image_data)

    return image_path

def change_zoom_background(image_path):
    background_name = "5E7B1C1B-BD7D-4852-B637-1E0A4E3381F6"
    # Zoom backgrounds directory
    zoom_backgrounds_dir = os.path.expanduser('~/Library/Application Support/zoom.us/data/VirtualBkgnd_Custom')

    # Path to the existing background image
    existing_background_path = os.path.join(zoom_backgrounds_dir, background_name)

    # Replace the existing background image with the new image
    if os.path.exists(existing_background_path):
        shutil.copyfile(image_path, existing_background_path)
#        print(f"Replaced {existing_background_path} with {image_path}")
    else:
        print(f"Background image {existing_background_path} not found.")

def daily_task():
    # Step 1: Lookup list of holidays
    data = holiday_lookup()

    # Step 2: Create image gen prompt with ChatGPT
    refined_prompt = refine_data_with_chatgpt(data)

    # Step 3: Generate Image with DALL-E
    image_path = generate_image_with_dalle(refined_prompt)

    # Step 4: Update Zoom to use new image
    change_zoom_background(image_path)

    # Send an email notification
    subject = "Zoom Background Changed Successfully"
    body = f"The daily task ran successfully.\n\nHolidays:\n{data}\n\nPrompt:\n{refined_prompt}\n\nGenerated Image path: {image_path}"
    send_email(subject, body)

# Example usage
# Run daily at 8AM with a cron job:
# 0 8 * * * /usr/bin/python3 /path/to/your_script.py
# Run weekdays at 7AM with a cron job:
# 0 7 * * 1-5 /usr/bin/python3 /path/to/your_script.py

if __name__ == "__main__":
    daily_task()

