from app import create_app, db
from app.models.user import User
from app.models.coin import Coin
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Coin': Coin, 'Portfolio': Portfolio, 'Transaction': Transaction}

if __name__ == '__main__':
    app.run(debug=True)
