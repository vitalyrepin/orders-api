# Order management interface
# Vitaly Repin

namespace * Metida

/**
  * Person: Name, Surname, Middle name and (optiona) Title (Mr., Mrs., Dr. etc)
 */
struct Person {
	1: string name,
	2: string surname,
	3: string middleName = "",
	4: optional string title
}

/**
 * Delivery address. Only ISO/IEC 8859-15 characters are allowed
 * <dl>
 * <dt>cc</dt> <dd>Country code according to ISO 3166-1 alpha-2</dd>
 * </dl>
 */
struct Address {
	1: Person to,
	2: string city,
	3: optional string state = "",
	4: string addressLine1,
	5: string addressLine2 = ""
	6: i64 zip,
	7: string cc
}

/**
 * Possible delivery modes
 *
 * <dl>
 * <dt>ECONOMY</dt> <dd>Economy-class delivery</dd>
 * <dt>COURIER_UPS</dt> <dd> Courier delivery: UPS carrier service </dd>
 * </dl>
 */
enum DeliveryMode {
	ECONOMY = 1,
	COURIER_UPS = 2
}

/**
 * Possible packaging modes
 *
 * <dl>
 * <dt>ENVELOPE</dt> <dd>Envelop</dd>
 * <dt>BOX</dt> <dd>Box</dd>
 * </dl>
 */
enum PackagingMode {
	ENVELOPE = 1,
	BOX = 2
}

/**
 * Possible status of the printing orders
 * <dl>
 * <dt>RECEIVED</dt> <dd>The order has been received</dd>
 * <dt>PAUSED</dt> <dd>The order has been paused (e.g., to clarify something with the customer)</dd>
 * <dt>PROCESSING</dt> <dd>The order is currently being processed by the stuff</dd>
 * <dt>MANUFACTURED</dt> <dd>The order has been manufactured</dd>
 * <dt>SHIPPED</dt> <dd>The order has been shipped</dd>
 * <dt>COMPLETED</dt> <dd> The order is completed</dd>
 * </dl>
 */
enum OrderStatus {
        RECEIVED = 1
	PAUSED = 2,
	PROCESSING = 3,
	MANUFACTURED = 4,
	SHIPPED = 5,
	COMPLETED = 6
}

/**
 * Possible profile parameters
 * <dl>
 * <dt>CBK_URL</dt> <dd>Call back URL to be called when the order status is changed.</dd>
 * </dl>
 */
enum ProfileParam {
	CBK_URL = 1
}

/**
 * Possible error codes for order-related errors
 *
 * <dl>
 * <dt>INVALID_ID</dt> <dd> Operation on non-existing order is requested </dt>
 * <dt>INVALID_ADDRESS</dt> <dd> Delivery is requested to the destination which is currently not served </dd>
 * <dt>INVALID_PRINT_URL</dt> <dd> Service can't download the file to print using the URL given</dd>
 * <dt>MD5_SUM_MISMATCH</dt> </dd> Mismatch of MD5 sum for the downloaded document </dd>
 * </dl>
 */
enum OrderErrCode {
	INVALID_ID = 1,
	INVALID_ADDRESS = 2,
	INVALID_PRINT_URL = 3,
	MD5_SUM_MISMATCH =4
}

/**
 * Shipment details for the order
 * <dl>
 * <dt>address</dt> <dd> Delivery address </dd>
 * <dt>deliveryMode</dt> <dd>Delivery class (economy, courier)</dd>
 * <dt>packagingMode</dt> <dd>Packaging selection</dd>
 * </dl>
 */
struct ShipmentData {
	1: Address address,
	2: DeliveryMode deliveryMode,
	3: PackagingMode packagingMode
}

/**
 * Details of the product to be ordered. Products codes are published at our web site.
 * <dl>
 * <dt>productCode</dt> <dd>Product code from the product catalog</dd>
 * <dt>qty</dt> <dd> Number of the product copies to manufacture</dd>
 * <dt>url</dt> <dd> URL to fetch the document to print from</dd>
 * <dt>md5</dt> <dd> MD5 sum of the document located at the URL url</dd>
 * </dl>
 */
struct ProductData {
	1: string productCode,
	2: byte qty
	3: string url
	4: string md5
}

/**
 * Miscellaneous order details to be stored with the order. Optional
 * <dl>
 * <dt>docId<dt> <dd> Internal document id used by Customer </dd>
 * <dt>comment</dt> <dd> Any text remark about the order </dd>
 * </dl>
 */
struct OrderMiscDetails {
	1: string docId
	2: string comment
}

/**
 * OrderStatus / Time pair
 * <dl>
 * <dt>tm</dt> <dd>Unix timestamp - number of seconds since UNIX epoch</dd>
 * </dl>
 */
struct OrderTimePair {
	1: i64 tm,
	2: OrderStatus status
}

/**
 *  Order processing errors
 *
 *  code:	Numerical error code
 *
 *  _message:	Human-readable error description
 */
exception OrderError {
	1: OrderErrCode code,
	2: string _message
}

/**
 *  This exception is used for general run-time errors
 *
 *  orderId:	Id of the order which caused error
 *
 *  _message:	Human-readable error description
 */
exception GeneralError {
	1: string orderId,
	2: string _message
}

/**
 *  Access denied errors
 *
 *  _message:	Human-readable error description
 */
exception AccessDenied {
	1: string _message
}

/**
 *  Authentication token is expired. You need to re-request auth token using getAuthToken method
 *
 *  _message:	Human-readable error description
 */
exception AuthTokenExpired {
	1: string _message
}

/**
 * Service: OrderManager
 *
 * <p> This service is used to manage orders </p>
 */
service OrderManager {
	/**
	  * Returns authentication token to be used in all other methods
	  */
	string getAuthToken(1:string username, 2:string pswd) throws(1:AccessDenied adn)
	/**
	  * Pings the service
	 */
	void ping(1: string authToken) throws (1:AccessDenied ad_err, 2:AuthTokenExpired at_err)
	/**
	 * Puts new Purchase Order to the system. Returns order ID
	 *
	 * @param authToken  Authentication token returned by getAuthToken method
	 *
	 * @param shipment Shipment data (address, deliveryMode, packaging selection)
	 *
	 * @param productData Products to be manufactuired (typically this list contains 1 product)
	 *
	 * @param misc Miscellaneous details about the order (can be stored with the order and returned by getOrderDetails method
	 */
	string newOrder(1:string authToken, 2:ShipmentData shipment, 3:list<ProductData> productData, 4:OrderMiscDetails misc) throws (1:OrderError o_err, 2:GeneralError g_err, 3:AccessDenied ad_err, 4:AuthTokenExpired at_err)
	/**
	 * Returns all the details about specific order
	 *
	 * @param authToken  Authentication token returned by getAuthToken method
	 *
	 * @param orderId Id of the order (returned by the method newOrder)
	 */
	list<OrderTimePair>  getOrderDetails(1:string authToken, 2:string orderId) throws(1:OrderError o_err, 2:GeneralError g_err, 3:AccessDenied ad_err, 4:AuthTokenExpired at_err)
	/**
	 * Sets profile parameter
	 *
	 * @param authToken  Authentication token returned by getAuthToken method
         *
	 * @param param Parameter code
	 *
	 * @param value Value of parameter to set
	 */
	void setProfileParam(1:string authToken, 2:ProfileParam param, 3:string value) throws(1:AccessDenied ad_err, 2:GeneralError g_err, 3:AuthTokenExpired at_err)
	/**
	 * Gets profile parameter. Returns value of the profile parameter (as string).
	 *
	 * @param authToken  Authentication token returned by getAuthToken method
         *
	 * @param param Parameter code
	 */
	string getProfileParam(1:string authToken, 2:ProfileParam param) throws(1:AccessDenied ad_err, 2:GeneralError g_err, 3:AuthTokenExpired at_err)
}
