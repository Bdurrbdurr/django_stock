from django.shortcuts import render,redirect
import yfinance as yf
from .models import Stock
from .forms import StockForm
from django.contrib import messages

# Utility function to fetch stock data
def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)             # Pass the ticker symbol to yf.Ticker
    try:
        api = stock.history(period="5d")  # Get stock data
        if api.empty:  # Check if data is empty
            raise ValueError("No data found for the given symbol.")
        
        company_name = stock.info.get('longName', 'Company name unavailable')  # Get company name
        api.reset_index(inplace=True)  # Reset the index for better formatting
        api = api.to_dict(orient='records')  # Convert data to list of dictionaries
        
        return {
            'symbol': ticker,
            'company_name': company_name,
            'data': api
        }
    except Exception as e:          
        return str(e)  # If any error occurs(invalid ticker), returns error message as a string

def home(request):
    
    company_name = None                  # company_name is set to None at the start of the function. This ensures it exists in all control paths, even if the try block or POST logic fails.
    
    if request.method == 'POST':
        ticker = request.POST.get('ticker').strip()  # Strip whitespace while input from user
        #symbol = 'AAPL'                 # Hardcoding stock symbol (Apple Inc. for valid test, invalid for error testing).
        
        # Validate the ticker symbol if its non-empty
        if not ticker:
            messages.error(request, "Ticker symbol cannot be empty! Please enter a valid ticker symbol.")
            return render(request, 'home.html')  # Re-render the form with an error message
        
        stock = yf.Ticker(ticker)           ## Create yfinance object for the ticker symbol. Fetch stock data using yfinance. Fetch data for the last 5 days (by default it's 1 month; when nothing is passed)  
                                            ## (Can also use fetch_stock_data function alternatively!)
        try:
            api = stock.history(period="5d") # history() returns a Pandas DataFrame with historical stock price data                             
            if api.empty:                    # Check if the DataFrame is empty. The .empty property only works with a Pandas DataFrame
                raise ValueError("No data found for the given symbol.")
        
            company_name = stock.info.get('longName', 'Company name unavailable')   # To fetch the company name for ticker symbol from API; stock.info fetches metadata from Yahoo Finance. If the API is unable to retrieve company details, it gracefully defaults to "Company name unavailable".
            api.reset_index(inplace=True)    # The Date column is likely the index of the DataFrame, not a regular column. By default, when you convert a Pandas DataFrame to a dictionary with .to_dict(orient='records'), only the column data is included in the dictionaries. The index is excluded unless explicitly reset or included.
                                             # To include the Date in your dictionaries, reset the index before converting the DataFrame. Moves the index (Date) to a regular column.
            api = api.to_dict(orient='records') # Convert the DataFrame to a list of dictionaries for the template
                                             # In Pandas, the orient parameter is used when converting a DataFrame to a JSON or dictionary format. When you use orient='records', the output is structured as a list of dictionaries, where each dictionary represents a row in the DataFrame, and the keys are the column names.
        except Exception as e:
            api = f"Error occurred: {str(e)}"    # Handle errors and pass an error message to the template  
        return render(request,'home.html',{'api': api, 'ticker': ticker, 'company_name': company_name})
     
    # For GET requests, provide an initial message to show on the page
    return render(request, 'home.html', {'ticker_message': "Enter the ticker symbol above to get stock data!"}) 

def about(request):
    return render(request,'about.html',{})
    
def add_stock(request):
    # Initialize tickers_list at the start for both POST and GET requests
    tickers_list = Stock.objects.all()  # Get all stock objects (queryset) from the database
    output = []
    
    # Fetch stock data for the existing tickers
    for ticker_item in tickers_list:                            # Loop through tickers to get stock data
        stock_data = fetch_stock_data(ticker_item.ticker)
        if isinstance(stock_data, str):  # Check if the result is an error message (a string)
            messages.error(request, f"Error fetching data for ticker {ticker_item.ticker}: {stock_data}")
            continue  # Continue to the next ticker if there's an error
        else:
            output.append(stock_data)  # Add valid stock data to output list
    
    # For GET request, return the form and existing stock data
    if request.method == 'GET':
        form = StockForm()  # Initialize the form for GET requests
        
    # For POST request, handle form submission and ticker validation to add new stock
    else:
        form = StockForm(request.POST)

        if form.is_valid():
            ticker = form.cleaned_data.get('ticker').strip()  # Get cleaned ticker input
            
            # Check if the ticker already exists in the database
            if Stock.objects.filter(ticker=ticker).exists():  # Look for a matching ticker in the database
                messages.error(request, f"Ticker already exists in the database.")
                return render(request, 'add_stock.html', {'form': form, 'ticker': tickers_list, 'output': output})

            # Fetch stock data for the new ticker
            stock_data = fetch_stock_data(ticker)
            
            if isinstance(stock_data, str):  # Check if the result is a string (error message from fetch_stock_data)
                messages.error(request, f"Error occurred due to invalid stock ticker '{ticker}': {stock_data}")
            elif stock_data:  # If valid data is returned (not a string and not empty)
                new_stock = form.save()  # Save the new stock to the database
                messages.success(request, f"Stock {ticker} has been added!")
                return redirect('add_stock')  # After successful submission, reload the data to show the newly added stock
            #else:  # If stock_data is empty or None (meaning the data fetch failed)
                #messages.error(request, f"Failed to fetch data for ticker '{ticker}'.")
        else:
            # This will only run if the form is invalid, i.e., if the ticker is empty
            messages.error(request, "Form is not valid, please check your input.")

    # Return the template with both the form and the stock data
    return render(request, 'add_stock.html', {'form': form, 'ticker': tickers_list, 'output': output})

def delete(request, stock_id):
    item = Stock.objects.get(pk=stock_id)
    item.delete()
    messages.success(request, ("Stock has been deleted!"))
    return redirect(delete_stock)

def delete_stock(request):
    ticker = Stock.objects.all()
    return render(request,'delete_stock.html',{'ticker': ticker})