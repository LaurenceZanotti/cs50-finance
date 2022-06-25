# CS50 Finance

![Demo image](https://raw.githubusercontent.com/LaurenceZanotti/cs50-finance/assets/cs50finance-mockup.png)

CS50 Finance permite que você cote, compre e venda ações. Comece com $10.000 e tente lucrar! (É uma simulação, claro) Você também pode visualizar os preços das ações em tempo real e o histórico da conta.

Mais informações sobre o projeto podem ser encontradas nas [especificações do CS50](https://cs50.harvard.edu/x/2022/psets/9/finance/).

Veja o projeto ao vivo no https://pacific-dawn-05944.herokuapp.com/

Este projeto é a minha apresentação para o Problem Set 9 do curso de Introdução ao CS50 de Ciência da Computação de Harvard, que eu cursei em 2020.

## Instalação

Crie e ative o ambiente virtual

    python -m venv venv
    source venv/bin/activate

Vá para https://iexcloud.io/cloud-login#/register/ e crie uma conta.

Obtenha uma chave de API em https://iexcloud.io/console/tokens. **(Não se esqueça de ativar o modo sandbox antes de copiar a chave de API)**

    pip install -r requirements.txt
    export FLASK_APP=application
    export API_KEY=<your_iex_exchange_api_key>

Finalmente, execute o aplicativo

    flask run

Crie uma conta e faça login com ela. Agora você pode cotar, comprar e vender ações.