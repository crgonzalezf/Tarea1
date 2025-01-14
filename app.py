from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap5
from openai import OpenAI
from dotenv import load_dotenv
from db import db, db_config
from models import User, Message

load_dotenv()

client = OpenAI()
app = Flask(__name__)
bootstrap = Bootstrap5(app)
db_config(app)


@app.route('/')
def index():
    return render_template('landing.html')



@app.route('/chat', methods=['GET', 'POST'])
def chat():
    user = db.session.query(User).first()

    if request.method == 'GET':
        return render_template('chat.html', messages=user.messages)

    intent = request.form.get('intent')

    intents = {
        'Quiero tener suerte': 'Recomiéndame una película',
        'Recomiéndame una de Suspenso': 'Recomiéndame una película de suspenso',
        'Recomiéndame Documentales': 'Recomiéndame documentales',
        'Recomiéndame una de Drama': 'Recomiéndame una película de drama',
        'Enviar': request.form.get('message')
    }

    if intent in intents:
        user_message = intents[intent]

        # Guardar nuevo mensaje en la BD
        db.session.add(Message(content=user_message, author="user", user=user))
        db.session.commit()


        messages_for_llm = [{
            "role": "system",
            "content": (
            f"Eres un chatbot llamado 'CineBot' que recomienda películas. "
            f"Tu usuario tiene una película favorita llamada '{user.favorite_movie}' "
            f"y su género favorito es '{user.favorite_genre}'. "
            f"Usa esta información para proporcionar recomendaciones personalizadas. "
            f"Tu rol es responder de manera breve y concisa."
        ),
        }]
        
      
        for message in user.messages:
            messages_for_llm.append({
                "role": message.author,
                "content": message.content,
            })

        chat_completion = client.chat.completions.create(
            messages=messages_for_llm,
            model="gpt-4o",
            temperature=1
        )

        model_recommendation = chat_completion.choices[0].message.content
        db.session.add(Message(content=model_recommendation, author="assistant", user=user))
        db.session.commit()

        return render_template('chat.html', messages=user.messages)


@app.route('/user/<username>')
def user(username):
    favorite_movies = [
        'The Shawshank Redemption',
        'The Godfather',
        'The Dark Knight',
    ]
    return render_template('user.html', username=username, favorite_movies=favorite_movies)


@app.post('/recommend')
def recommend():
    user = db.session.query(User).first()
    data = request.get_json()
    user_message = data['message']
    new_message = Message(content=user_message, author="assistant", user=user)
    db.session.add(new_message)
    db.session.commit()

    messages_for_llm = [{
        "role": "system",
        "content": "Eres un chatbot que recomienda películas, te llamas 'CineBot'. Tu rol es responder recomendaciones de manera breve y concisa. No repitas recomendaciones.",
    }]

    for message in user.messages:
        messages_for_llm.append({
            "role": message.author,
            "content": message.content,
        })

    chat_completion = client.chat.completions.create(
        messages=messages_for_llm,
        model="gpt-4o",
    )

    message = chat_completion.choices[0].message.content

    return {
        'recommendation': message,
        'tokens': chat_completion.usage.total_tokens,
    }


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    try:
        user = db.session.query(User).first()

        if request.method == 'POST':
            # Recuperar datos del formulario
            favorite_movie = request.form.get('favorite_movie', '').strip()
            favorite_genre = request.form.get('favorite_genre', '').strip()

            # Validar y actualizar los datos
            if favorite_movie:
                user.favorite_movie = favorite_movie
            if favorite_genre:
                user.favorite_genre = favorite_genre

            db.session.commit()

            # Redirigir con un parámetro de confirmación
            return redirect('/profile?updated=true')

        # Verificar si se actualizó el perfil
        updated = request.args.get('updated', 'false') == 'true'

        return render_template('profile.html', user=user, updated=updated)
    except Exception as e:
        # Registrar el error en los logs y mostrar un mensaje de error genérico
        app.logger.error(f"Error en /profile: {e}")
        return "Ha ocurrido un error en el servidor. Por favor, inténtalo de nuevo más tarde.", 500


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            user = User(email=email, password_hash=bcrypt.generate_password_hash(password).decode('utf-8'))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('chat'))
    return render_template('sign-up.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            user = db.session.query(User).filter_by(email=email).first()
            if user and bcrypt.check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect('chat')

            flash("El correo o la contraseña es incorrecta.", "error")

    return render_template('log-in.html', form=form)


@app.get('/logout')
def logout():
    logout_user()
    return redirect('/')





