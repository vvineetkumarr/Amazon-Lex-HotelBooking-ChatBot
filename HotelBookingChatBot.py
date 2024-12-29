import json
from datetime import datetime

# Validation function
def validate(slots):
    if not slots.get('Location'):
        return {
            'isValid': False,
            'violatedSlot': 'Location',
            'message': "Which city would you like to book a hotel in?"
        }
    
    if not slots.get('CheckInDate'):
        return {
            'isValid': False,
            'violatedSlot': 'CheckInDate',
            'message': "When would you like to check in?"
        }
    
    try:
        check_in = datetime.strptime(slots['CheckInDate']['value']['interpretedValue'], '%Y-%m-%d')
        if check_in < datetime.now():
            return {
                'isValid': False,
                'violatedSlot': 'CheckInDate',
                'message': "Check-in date cannot be in the past. Please provide a valid date."
            }
    except (ValueError, KeyError):
        return {
            'isValid': False,
            'violatedSlot': 'CheckInDate',
            'message': "Invalid date format for Check-in date. Please provide a valid date in YYYY-MM-DD format."
        }
    
    if not slots.get('CheckOutDate'):
        return {
            'isValid': False,
            'violatedSlot': 'CheckOutDate',
            'message': "When would you like to check out?"
        }
    
    try:
        check_out = datetime.strptime(slots['CheckOutDate']['value']['interpretedValue'], '%Y-%m-%d')
        if check_out <= check_in:
            return {
                'isValid': False,
                'violatedSlot': 'CheckOutDate',
                'message': "Check-out date must be after the Check-in date. Please provide a valid date."
            }
    except (ValueError, KeyError):
        return {
            'isValid': False,
            'violatedSlot': 'CheckOutDate',
            'message': "Invalid date format for Check-out date. Please provide a valid date in YYYY-MM-DD format."
        }

    if not slots.get('RoomType'):
        return {
            'isValid': False,
            'violatedSlot': 'RoomType',
            'message': "What type of room would you like to book? We have Classic, Duplex, Suite, Premium Suite, and Luxury."
        }
    
    if not slots.get('NumberOfGuests'):
        return {
            'isValid': False,
            'violatedSlot': 'NumberOfGuests',
            'message': "How many guests will be staying?"
        }
    
    return {'isValid': True}

# Fare calculation function
def calculate_fare(check_in_date, check_out_date, number_of_guests, room_type):
    room_rate_per_night = {
    'Classic': 10,
    'Duplex': 15,
    'Suite': 20,
    'Premium Suite': 25,
    'Luxury': 50
    }
    
    check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
    check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
    num_nights = (check_out - check_in).days
    room_rate = room_rate_per_night.get(room_type, 10)
    
    total_fare = num_nights * room_rate * number_of_guests
    return total_fare

# Lambda handler
def lambda_handler(event, context):
    intent = None
    slots = {}

    try:
        slots = event['sessionState']['intent']['slots']
        intent = event['sessionState']['intent']['name']
        validation_result = validate(slots)

        room_rate_per_night = {
             'Classic': 10,
             'Duplex': 15,
             'Suite': 20,
             'Premium Suite': 25,
             'Luxury': 50
        }

        if event['invocationSource'] == 'DialogCodeHook':
            if not validation_result['isValid']:
                violated_slot = validation_result['violatedSlot']
                message = validation_result['message']
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": violated_slot
                        },
                        "intent": {
                            'name': intent,
                            'slots': slots,
                            'state': 'InProgress'
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": message
                        }
                    ]
                }

            if 'RoomTypeConfirmation' not in slots or not slots['RoomTypeConfirmation'] or not slots['RoomTypeConfirmation'].get('value'):
                room_type = slots['RoomType']['value']['interpretedValue']
                room_rate = room_rate_per_night.get(room_type, 100)
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": "RoomTypeConfirmation"
                        },
                        "intent": {
                            'name': intent,
                            'slots': slots,
                            'state': 'InProgress'
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": f"{room_type} rooms cost ${room_rate} per night. Do you wish to continue?"
                        }
                    ]
                }

            if slots['RoomTypeConfirmation']['value']['interpretedValue'].lower() not in ['yes', 'i confirm']:
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "Close",
                            "fulfillmentState": "Failed"
                        },
                        "intent": {
                            'name': intent,
                            'slots': slots,
                            'state': 'Failed'
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": "You did not confirm the room type. Please try again if you wish to make a reservation."
                        }
                    ]
                }

            if 'Confirmation' not in slots or not slots['Confirmation'] or not slots['Confirmation'].get('value'):
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "ElicitSlot",
                            "slotToElicit": "Confirmation"
                        },
                        "intent": {
                            'name': intent,
                            'slots': slots,
                            'state': 'InProgress'
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": f"Please confirm your reservation details: Check-in Date: {slots['CheckInDate']['value']['interpretedValue']}, Check-out Date: {slots['CheckOutDate']['value']['interpretedValue']}, Number of Guests: {slots['NumberOfGuests']['value']['interpretedValue']}, Room Type: {slots['RoomType']['value']['interpretedValue']}."
                        },
                        {
                            "contentType": "PlainText",
                            "content": "Type 'Yes' to confirm or 'No' to cancel."
                        }
                    ]
                }

            if slots['Confirmation']['value']['interpretedValue'].lower() in ['yes', 'i confirm']:
                total_fare = calculate_fare(
                    slots['CheckInDate']['value']['interpretedValue'],
                    slots['CheckOutDate']['value']['interpretedValue'],
                    int(slots['NumberOfGuests']['value']['interpretedValue']),
                    slots['RoomType']['value']['interpretedValue']
                )
                return {
                    "sessionState": {
                        "dialogAction": {
                            "type": "Close",
                            "fulfillmentState": "Fulfilled"
                        },
                        "intent": {
                            'name': intent,
                            'slots': slots,
                            'state': 'Fulfilled'
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": f"Thank you for confirming your reservation! Your total fare is ${total_fare}. We look forward to your stay."
                        }
                    ]
                }

            return {
                "sessionState": {
                    "dialogAction": {
                        "type": "Close",
                        "fulfillmentState": "Failed"
                    },
                    "intent": {
                        'name': intent,
                        'slots': slots,
                        'state': 'Failed'
                    }
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": "Reservation was not confirmed. Please try again if you wish to make a reservation."
                    }
                ]
            }

    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "sessionState": {
                "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Failed"
                },
                "intent": {
                    'name': intent if intent else 'Unknown',
                    'slots': slots if slots else {},
                    'state': 'Failed'
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "An error occurred while processing your request. Please try again."
                }
            ]
        }

# Testing
def test_lambda_handler():
    mock_event = {
        "sessionState": {
            "intent": {
                "name": "BookHotel",
                "slots": {
                    "Location": {"value": {"interpretedValue": "Mumbai"}},
                    "CheckInDate": {"value": {"interpretedValue": "2025-01-01"}},
                    "CheckOutDate": {"value": {"interpretedValue": "2025-01-05"}},
                    "NumberOfGuests": {"value": {"interpretedValue": "3"}},
                    "RoomType": {"value": {"interpretedValue": "Suite"}},
                    "RoomTypeConfirmation": {"value": {"interpretedValue": "yes"}},
                    "Confirmation": {"value": {"interpretedValue": "yes"}}
                }
            }
        },
        "invocationSource": "DialogCodeHook"
    }
    
    response = lambda_handler(mock_event, None)
    print(json.dumps(response, indent=4))

# Run the test
test_lambda_handler()
