import requests
from datetime import datetime
from sanic import Sanic
from sanic.response import json
from sanic_cors import CORS, cross_origin
from sanic.handlers import ErrorHandler
from sanic.exceptions import SanicException
from sanic_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    create_refresh_token)
from sanic_jwt_extended.exceptions import JWTExtendedException
from sanic_jwt_extended.tokens import Token
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
PORT = 7777
handler = CustomHandler()
app.error_handler = handler
jwt = JWTManager(app)
app.blueprint(swagger_blueprint)
CORS(app, automatic_options=True)
Compress(app)

########################################### SWAGGER CONFIG####################################
app.config.API_BASEPATH="/"
app.config.API_SCHEMES = ["http"]
app.config.API_VERSION = '1.0.0'
app.config.API_TITLE = 'Paystand Integration'
app.config.JWT_SECRET_KEY = "af8f6225-ec38-4bf3-b40c-29642ccd6312"
app.config.JWT_ACCESS_TOKEN_EXPIRES = False
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
        "tokenUrl": "https://api.paystand.co/v3/oauth/token",
        "scopes": {"client_credentials": "Grants access to this API"},
    }
}

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

class Settings: 
    enabled = doc.Boolean("Events enabled")
    urls = doc.List("URLS for events to be sent to.")

class AdditionalOwner: 
    id = doc.String("The unique identifier for the additional owner.")
    object = doc.String("Value is legalEntityAdditionalOwner")
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
    id = doc.String("The unique identifier for the bank.")
    object = doc.String("Value is bank.")
    accountType = doc.String("The account type of the bank.")
    bankName = doc.String("The bank name.")
    routingNumber = doc.String("The bank routing number.")
    accountNumber = doc.String("The bank account number.")
    nameOnAccount = doc.String("The name on the bank account.")
    accountHolderType = doc.String("The account holder type for the bank")
    currency = doc.String("The currency of the bank")
    country = doc.String("The country for the bank")
    last4 = doc.String("The last four digits of the account number")
    fingerprint = doc.String("The unique identifier for the routing and account number.")
    isDefault = doc.Boolean("Is a default bank")
    isApDefault = doc.Boolean("Is a default AP bank")
    billingAddress = doc.Object(Address,"The billing address associated with the bank")
    externalId = doc.String("An external id for the bank.")
    dropped = doc.Boolean("Has the bank been two-dropped")
    verified = doc.Boolean("verified")
    status = doc.String("Possible values: active, inactive. Active: The bank is active and able to be used to make payments, Inactive: The bank is not active and is unable to be used to make payments.")
    created = doc.Date("The date the bank was created")
    lastUpdated = doc.Date("The date the bank was last updated.")

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
########################################### ENDPOINTS ####################################################### 

@doc.tag("Create Paystand network access token")
@doc.summary("Access Token format is Bearer: token")
@doc.consumes(TokenReq)
@app.route("/paystand/token")

async def get_accesstoken(request):
    data = request.json
    res = requests.post("https://api.paystand.co/v3/oauth/token",json=data)
    return json(res.json())

@doc.tag("Create Customer")
@doc.summary("Create customer to use Paystand network: A customer can send and receive payments, create and track receivables, manage their accounts, withdrawal funds.")
@doc.consumes(CustomerReg)
@app.route("/paystand/customer")
async def customer(request,token : Token):
    data = request.json
    return json({"hello": "world"})

@app.route("/yapily/ach2")
async def test1(request):
  return json({"hello": "world"})

@app.route("/yapily/ach3")
async def test2(request):
  return json({"hello": "world"})

@app.route("/yapily/ach")
async def test3(request):
  return json({"hello": "world"})

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=PORT)