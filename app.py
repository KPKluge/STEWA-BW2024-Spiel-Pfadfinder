from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time, timezone

# Initialisierung der Flask-App und der Datenbank
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///players.db'
db = SQLAlchemy(app)

# Funktion, die die aktuelle Zeit zurückgibt und dabei die Sekunden und Mikrosekunden auf 0 setzt
def current_time():
    now = datetime.now()
    return now.replace(second=0, microsecond=0)

# Datenbank-Modell für die Spieler/Gruppen
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=current_time)
    red_pearls = db.Column(db.Integer, default=0)
    green_pearls = db.Column(db.Integer, default=0)
    blue_pearls = db.Column(db.Integer, default=0)

# Route für die Startseite, die alle Spieler/Gruppen anzeigt und die Möglichkeit bietet, neue Spieler/Gruppen hinzuzufügen
@app.route('/', methods=['GET'])
def index():
    players = Player.query.order_by(Player.timestamp).all()
    return render_template('index.html', players=players)

# Route für das Hinzufügen eines neuen Spielers/einer neuen Gruppe
@app.route('/player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        number = request.form.get('number')
        new_player = Player(number=number)
        db.session.add(new_player)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

# Route um die Perlen eines Spielers/Gruppe zu aktualisieren
@app.route('/pearls', methods=['GET', 'POST'])
def update_pearls():
    if request.method == 'POST':
        player_number = request.form.get('player_number')
        red_pearls = request.form.get('red_pearls')
        green_pearls = request.form.get('green_pearls')
        blue_pearls = request.form.get('blue_pearls')

        player = Player.query.filter_by(number=player_number).first()
        if player:
            player.red_pearls += int(red_pearls)
            player.green_pearls += int(green_pearls)
            player.blue_pearls += int(blue_pearls)
            db.session.commit()
            return redirect(url_for('update_pearls'))
        else:
            return 'Player not found', 404
    else:
        players = Player.query.order_by(Player.timestamp).all()
        for player in players:
            player.timestamp = player.timestamp.strftime('%H:%M')
        return render_template('pearls.html', players=players)

# Route zum Darstellen der Spieler/Gruppen und ihrer Perlen
@app.route('/pearls', methods=['GET', 'POST'])
def pearls():
    players = Player.query.order_by(Player.timestamp).all()
    for player in players:
        player.timestamp = datetime.strptime(player.timestamp, '%H:%M.%f')  # Convert string to datetime
    return render_template('pearls.html', players=players)

# Route zum Beenden des Spiels und Berechnen der Punkte
@app.route('/end_game', methods=['GET', 'POST'])
def end_game():
    end_time = datetime.combine(datetime.today(), time())  # Standardwert für die Endzeit ist die aktuelle Uhrzeit
    if request.method == 'POST':
        end_time_str = request.form.get('end_time')
        end_time = datetime.strptime(end_time_str, '%H:%M')
        end_time = end_time.replace(year=datetime.today().year, month=datetime.today().month, day=datetime.today().day) # Setzt das Datum der Endzeit auf den heutigen Tag, da Default 01.01.1900 ist

        # Berechnung der Punkte für jeden Spieler/Gruppe
        players = Player.query.all()
        for player in players:
            player.score = (player.red_pearls + player.green_pearls + player.blue_pearls) * 5   # 5 Punkte pro Perle
            player.score += min(player.red_pearls, player.green_pearls, player.blue_pearls) * 10    # 10 Bonuspunkte für jede Perle in allen Farben
            late_minutes = int((player.timestamp - end_time).total_seconds() / 60)  # Berechnet die Verspätung in Minuten
            player.late_minutes = late_minutes
            if late_minutes > 0:
                player.score -= late_minutes * 5    # 5 Punkte Abzug pro Minute Verspätung 
        db.session.commit()
    return render_template('end_game.html', players=Player.query.all(), end_time=end_time)

# Route zum Löschen aller Spieler/Gruppen
@app.route('/clear_db', methods=['GET', 'POST'])
def clear_db():
    if request.method == 'POST':
        db.session.query(Player).delete()
        db.session.commit()
        return "Database cleared"
    return render_template('confirm_clear_db.html')

# Starten der Flask-App
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

