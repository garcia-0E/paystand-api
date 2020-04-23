import requests
import uuid
from datetime import datetime
from sanic import Sanic
from sanic.response import json
from sanic.log import logger
from sanic_cors import CORS, cross_origin
from sanic.handlers import ErrorHandler
from sanic.exceptions import SanicException
from motor.motor_asyncio import AsyncIOMotorClient
from sanic.exceptions import ServerError
from sanic_openapi import swagger_blueprint
from sanic_openapi import doc
from sanic_compress import Compress


class CustomHandler(ErrorHandler):
    def default(self, request, exception):
        print("[EXCEPTION] "+str(exception))
        return json('NO',501)  

app = Sanic(__name__)
PORT = 5555
handler = CustomHandler()
app.error_handler = handler
app.blueprint(swagger_blueprint)
CORS(app, automatic_options=True)
Compress(app)

########################################### SWAGGER CONFIG####################################
app.config.API_BASEPATH="/"
app.config.API_SCHEMES = ["http"]
app.config.API_VERSION = '1.0.0'
app.config.API_TITLE = 'Paystand Integration'
app.config.SWAGGER_UI_CONFIGURATION = {
    'validatorUrl': None,  # Disable Swagger validator
    'displayRequestDuration': True,
    'docExpansion': 'none',
    'defaultModelRendering': 'model'
}
app.config.API_SECURITY = [{"OAuth2": []}]
app.config.API_SECURITY_DEFINITIONS = {
    "OAuth2": {
        "type": "oauth2",
        "flow": "application", 
        "in": "header", 
        "name": "Authorization",
        "tokenUrl": "https://api.paystand.co/v3/oauth/token",
        "scopes": "auth"
    }
}
############################## MONGO CONNECTION ############################
def get_mongo_conn():
    MONGO_CONFIG = {
    "MONGO_HOST" : "35.221.170.100",
    "MONGO_PORT" : 27030,
    "MONGO_DB" : "paystand",
    #
     "MONGO_USER" : "paystand",
     "MONGO_PASSWORD" : "p4yst4nd..$",
    }
    client = {}
    mongo_uri = "mongodb://"+str(MONGO_CONFIG['MONGO_USER'])+":"+MONGO_CONFIG['MONGO_PASSWORD']+"@"+MONGO_CONFIG['MONGO_HOST']+":"+str(MONGO_CONFIG['MONGO_PORT'])+"/paystand"
    # mongo_uri = "mongodb://"+str(MONGO_CONFIG['MONGO_USER'])+":"+MONGO_CONFIG['MONGO_PASSWORD']+"@"+MONGO_CONFIG['MONGO_HOST']+":"+str(MONGO_CONFIG['MONGO_PORT'])+"/admin"
    client = AsyncIOMotorClient(mongo_uri)
    logger.info('Conectado a MongoDB...')
    return client['paystand']
############################## YAPILY KEYS #################################

APPLICATION_ID = "be32eb84-9045-4a8f-83e5-ccd24bdd9ec3" # YAPILY
APPLICATION_SECRET = "63d3f375-35c2-4cae-a5b1-9651248bfb23" # YAPILY


############################## PAYSTAND CLASSES ############################
class Address:
    street1 = doc.String("Street 1")
    street2 = doc.String("Street 2")
    city = doc.String("City")
    state = doc.String("State")
    postalCode = doc.String("Postal Code")
    country = doc.String("Country")

class Contact: 
    firstName= doc.String("Client first name")
    lastName = doc.String("Client last name")
    email = doc.String("Client email")
    phone = doc.String("Client phone")
    dateOfBirth = doc.String("Client birth date")

class AdditionalOwner: 
    # id = doc.String("The unique identifier for the additional owner.")
    # object = doc.String("Value is legalEntityAdditionalOwner")
    personalTaxId = doc.String("The personal tax id of the owner")
    last4PersonalTaxId = doc.String("The last 4 digits of the personal tax id of the owner. This is returned in responses instead of returning the full personal tax id.")
    stakePercent = doc.String("The stake percentage in the company for the additional owner.")
    title = doc.String("The title of the additional owner.")
    address = doc.Object(Address,"The address of the additional owner.")
    contact = doc.Object(Contact,"The contact of the additional owner.")
    created = doc.Date("The date the owner was created.")
    lastUpdated = doc.Date("The date the owner was last updated.")

class LegalEntity: 
    entityType = doc.String("Entity type: ISP,LLC,CORP. If the entityType is ISP, then the personalTaxId parameter should also be sent. The stakePercent parameter should be 100, and no additional owners will be allowed. If the entityType is LLC or CORP,  then the businessTaxId parameter should also be sent.")
    businessName = doc.String("This name is strictly for legal verification purposes. Under certain conditions this may be the same as merchant name.")
    businessTaxId = doc.String("The tax id belonging to the business.")
    businessSalesVolume = doc.String("The annual sales volume.")
    businessAcceptedCards = doc.String("Whether or not the business accepted card payments in the past or is currently accepting card payments.")
    yearsInBusiness= doc.String("The number of years this business has been operating.")
    personalTaxId = doc.String("The tax id for the owner of the business.")
    last4PersonalTaxId = doc.String("The last 4 digits of the tax id for the owner of the business.")
    businessAddress = doc.Object(Address,"The address of the legal entity.")
    personalAddress = doc.Object(Address,"The address of the primary contact for the legal entity.")
    personalContact = doc.Object(Contact,"The details of the primary contact for the legal entity.")
    stakePercent = doc.String("The primary owner's stake in the entity.")
    additionalOwners = doc.Object(AdditionalOwner,"Any additional owners of the entity.")

class Bank: 
    # id = doc.String("The unique identifier for the bank.")
    # object = doc.String("Value is bank.")
    accountType = doc.String("The account type of the bank.")
    bankName = doc.String("The bank name.")
    routingNumber = doc.String("The bank routing number.")
    accountNumber = doc.String("The bank account number.")
    nameOnAccount = doc.String("The name on the bank account.")
    accountHolderType = doc.String("The account holder type for the bank")
    currency = doc.String("The currency of the bank")
    country = doc.String("The country for the bank")
    billingAddress = doc.Object(Address,"The billing address associated with the bank")

class Merchant: 
    businessName = doc.String("The name of the business.")
    businessUrl = doc.String("The URL for the business's website.")
    businessLogo = doc.String("The URL for the business's logo.")
    supportEmail = doc.String("The support email for the business.")
    supportPhone = doc.String("The support phone number for the business.")
    supportUrl = doc.String("The URL to reach the support website for the business.")
    productDescription = doc.String("A description of the business's product.")
    statementDescriptor = doc.String("The statement descriptor that will show up on a payer's bank statement when processing through your Paystand network. Length 1-20. Valid Characters: [0-9, a-z, A-Z, &, *, #, period, comma, and space]")
    defaultCurrency = doc.String("The default currency that will be set for this customer. According to  ISO4217 currency code")
    merchantCategoryCode = doc.String("MCC is used to classify a business by the type of goods or services it provides.")
    bank = doc.Object(Bank,"The bank account information for this merchant.")
    businessAddress = doc.Object(Address,"The address for this business.")
    personalContact = doc.Object(Contact,"The personal contact for this business.")

class CustomerReg:
    name = doc.String("The full name of the customer.")
    email = doc.String("A valid email for the customer.")
    planKey = doc.String("The planKey you would like to use for this customer. Valid planKeys will be provided by Paystand.")
    vanityName = doc.String("The vanity name is a unique key used for providing public access to a billing portal.")
    description = doc.String("An optional description you can attribute to this customer.")
    address = doc.Object(Address,"The address of the customer.")
    contact = doc.Object(Contact, "The contact information for the customer.")
    defaultBank = doc.Object(Bank, "The default bank used for this customer. This can be used for withdrawing funds, and optionally can be used to pay subscription fees.")
    legalEntity = doc.Object(LegalEntity, "Detailed information about the legal entity for this customer.")
    merchant = doc.Object(Merchant, "Detailed information about the business this customer represents.")
    username = doc.String("The login name used for an optional user created with this customer.")
    password = doc.String("The password used for an optional user created with this customer.")

class TokenReq: 
    grant_type = doc.String("client_credentials")
    client_id = doc.String("Provided by Paystand")
    client_secret = doc.String("Provided by Paystand")
    scope = doc.String("auth")

class AmountVerification:
    customerName = doc.String("Customer that wants to be verified")
    amounts = doc.List("Amounts that were dropped")

class Payer:
    name = doc.String("The name of the payer.")
    email = doc.String('The email of the payer.')
    address = doc.Object(Address, "The address of the payer")

class PayerBank:
    payer_id = doc.String("The id of the payer that bank will be added")
    bank = doc.Object(Bank,"Bank object")

class Card:
    nameOnCard = doc.String('The name on the card')
    cardNumber = doc.String('The number of the card')
    expirationMonth = doc.String('The expiration month of the card.')
    expirationYear = doc.String('The expiration year of the card.')
    securityCode = doc.String('The security code of the card.')
    billingAddress = doc.Object(Address,'The billing address associated with the card.')

class PayerCardPayment:
    amount = doc.String("The amount of the payment")
    currency = doc.String('The currency of the payment')
    card = doc.Object(Card,'Card object that will be used')
########################################### ENDPOINTS ####################################################### 

@doc.tag("Create Paystand network access token")
@doc.summary("Access Token format is Bearer: token")
@doc.consumes(TokenReq, location="body", content_type='application/json')
@app.route("/paystand/token",['POST'])

async def get_accesstoken(request):
    data = request.json
    res = requests.post("https://api.paystand.co/v3/oauth/token",json=data)
    return json(res.json())

@doc.tag("Create Customer")
@doc.summary("Create customer to use Paystand network: A customer can send and receive payments, create and track receivables, manage their accounts, withdrawal funds.")
@doc.consumes(CustomerReg,location="body", content_type='application/json',)
@app.route("/paystand/customer",['POST'])
async def customer(request):
    data = request.json
    db = get_mongo_conn()

    customer = {
        "defaultBank":data['defaultBank'],
        "name":data['name'],
        "email":data['email']
    }

    r = requests.post("https://api.paystand.co/v3/customers/accounts",data,headers=request.header)
    if r.content['account']:
        customer['bank_id'] = r.content['id']
        await db.customer.insert_one(customer)
        logger.info("Comercio añadido con éxito")
        return json({'msg':'success',
                    'data':r.content})
    return json('ERROR')


@doc.tag("Drop amounts")
@doc.summary("Drop amounts for Bank account verification")
@doc.consumes(doc.String('customer Name', name='customerName'))
@app.route("/dropAmounts",['POST'])
async def dropAmounts(request):
    data = request.json
    db = get_mongo_conn()

    customer = db.customer.find_one({'name':data['customerName']},{'_id':0,'id':1})

    r = requests.post("https://api.paystand.co/v3/banks/{bank}/drops".format(bank=customer['id']))
    if (r.content['dropped']):
        return json('Succesfully dropped')
    return json('ERROR')

@doc.tag("Verificate Account")
@doc.summary("Bank account verification")
@doc.consumes(AmountVerification, location="body", content_type='application/json')
@app.route("/verificateAmounts",['POST'])
async def verifyAmounts(request):
    data = request.json
    db = get_mongo_conn()

    customer = db.customer.find_one({'name':data['customerName']},{'_id':0,'id':1})

    r = requests.post("https://api.paystand.co/v3/banks/{bank}/drops".format(bank=customer['id']),data['amounts'])
    if (r.content['verified']):
        return json('Succesfully verified')
    return json('ERROR')

@doc.tag("Create Payer")
@doc.summary("Payers are people or businesses that are able to pay a customer. Payers can hold cards and banks that can be used to create future payments. ")
@doc.consumes(Payer,location="body", content_type='application/json')
@app.route("/payer",['POST'])
async def payer(request):
    data = request.json
    db = get_mongo_conn()

    r = requests.post("https://api.paystand.com/v3/payers",data=data)
    
    if (r.content['id']):
        data['id'] = r.content['id']
        data['status'] = r.content['status']
        await db.payer.insert_one(data)
        return json({'msg':'success',
                     'data':data})
    return json('ERROR')

@doc.tag("Create Payer bank")
@doc.summary("Payer banks belong to specific payers and can be used to make payments.")
@doc.consumes(PayerBank,location="body", content_type='application/json')
@app.route("/payer/bank",['POST'])
async def payer_bank(request):
    data = request.json
    db = get_mongo_conn()

    bank_data = data['bank']
    payer = await db.payer.find_one({'id':data['payer_id']},{'_id':0})
    
    r = requests.post("api.paystand.com/v3/payers/{id}/banks".format(id=payer['id']),data=bank_data)
    
    if (r.content['object'] == 'bank'):
        await db.payer.update_one({'id':payer['id']} , {'$set': {'bank':r.content}})
        return json({'msg':'success',
                     'data':payer})
    return json('ERROR')

@doc.tag("Create payer card payment")
@doc.summary("The payment resource allows you to accept Card and Bank account payments.")
@doc.consumes(PayerCardPayment,location="body", content_type='application/json')
@app.route("/payer/card",['POST'])
async def payer_card(request):
    data = request.json
    r = requests.post('https://api.paystand.co/v3/payments/secure',data = data)

    if (r.content['object'] == 'payment'):
        return json({'msg':'success',
                     'data':r.content})
    return json('ERROR')


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=PORT)