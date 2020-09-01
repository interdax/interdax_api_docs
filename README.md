
# Interdax API
- Detailed API-docs with node.js and python code examples @ https://app.interdax.com/docs  
- A comprehensive example market-maker bot, utilizing both http and websocket API's is below

#### Example market-maker bot
##### Prerequisites
- Create an API-key in your account's security settings on the site: 
  - [Live](https://app.interdax.com)
  - [Testnet](https://test.interdax.com)  

- Install required python modules
  - `cd examples/python && pip install -r examples/python/requirements.txt`

##### Test  
> Runs a single market-making loop, cancels all orders and exits.  
- `python mmbot.py -as <YOUR-API-KEY-SECRET> -ak <YOUR-API-KEY-ID> -t`   

##### Run 
> Run a market-**making** infinite loop 
- `python mmbot.py -as <YOUR-API-KEY-SECRET> -ak <YOUR-API-KEY-ID> --market-maker`

> Run a market-**taking** loop that rebalances 50x leverage every 10 seconds
- `python mmbot.py -as <YOUR-API-KEY-SECRET> -ak <YOUR-API-KEY-ID> --market-taker --leverage 50 --delay 10`
 
##### Alternatively, use the docker image 
1.  Build - `cd examples/python && docker build . -t interdaxapi`  
2.  Test - `docker run -it -e API_KEY_SECRET=<YOUR-API-KEY-SECRET> -e API_KEY_ID=<YOUR-API-KEY-ID>  -e TEST=true interdaxapi`
3.  Run - `docker run -it -e API_KEY_SECRET=<YOUR-API-KEY-SECRET> -e API_KEY_ID=<YOUR-API-KEY-ID> interdaxapi`
