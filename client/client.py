from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests


if __name__ == '__main__':
    # init driver
    driver = webdriver.Chrome(executable_path='./chromedriver')

    ## create test user
    driver.get('http://localhost:3000/logintestuser/1000')
    # go to admin page to see created test user row
    driver.get('http://localhost:3000/admin/user')
    elems = driver.find_elements_by_class_name('col-userid')
    assert(any(e.text == '1000' for e in elems) == True)

    ## deposit money to balance 
    # go to profile page of user
    driver.get('http://localhost:3000/profile')
    # get current balance
    balance_prev = driver.find_element_by_class_name('balance-text').text
    balance_prev = int(balance_prev)
    # get button to deposit money
    form_deposit_money = driver.find_element_by_class_name('deposit')
    form_deposit_money.submit() # adds 100$
    # get new balance
    balance_after = driver.find_element_by_class_name('balance-text').text
    balance_after = int(balance_after)
    assert(balance_prev + 100 == balance_after)

    ## edit user name
    # get input field of name
    input_name_edit = driver.find_element_by_id('name')
    input_name_edit.clear()
    input_name_edit.send_keys('I am not a Bot!')
    # save data
    form_edit_profile_info = driver.find_element_by_class_name('edit-form')
    form_edit_profile_info.submit()
    # check new data in admin site
    driver.get('http://localhost:3000/admin/user')
    elems = driver.find_elements_by_class_name('col-name')
    assert(any(e.text == 'I am not a Bot!' for e in elems) == True)

    ## buy a product
    # choose what to buy and amount
    buy_product_id = 2
    buy_amount = 2
    # get current balance and currnet number of orders
    driver.get('http://localhost:3000/profile')
    balance_prev = int(driver.find_element_by_class_name('balance-text').text)
    count_orders_prev = len(driver.find_elements_by_class_name('order-data'))
    # go to product list page
    driver.get('http://localhost:3000/')
    # get price per piece of product to buy
    price = int(driver.find_element_by_id('price' + str(buy_product_id)).text)
    # set amount to buy
    input_amount_edit = driver.find_element_by_id('amount' + str(buy_amount))
    input_amount_edit.clear()
    input_amount_edit.send_keys(buy_amount)
    # click on buy
    form_edit_profile_info = driver.find_element_by_id('form' + str(buy_product_id))
    form_edit_profile_info.submit()
    # check new balance and new order in order list
    driver.get('http://localhost:3000/profile')
    balance_after = int(driver.find_element_by_class_name('balance-text').text)
    assert(balance_prev - buy_amount * price == balance_after)
    count_orders_after = len(driver.find_elements_by_class_name('order-data'))
    assert(count_orders_prev + 1 == count_orders_after)
    # get amount of completed orders for future
    elems = driver.find_elements_by_class_name("order-status")
    completed_prev = len([s for s in elems if s.text == 'completed'])

    ## create new user who will be a seller
    driver.get('http://localhost:3000/logintestuser/2000')
    # set seller checkbox
    input_become_seller = driver.find_element_by_id('ifseller')
    input_become_seller.click()
    # click save
    form_edit_profile_info = driver.find_element_by_class_name('edit-form')
    form_edit_profile_info.submit()
    # check if user can visit seller page 
    driver.get('http://localhost:3000/sell')
    t = driver.find_element_by_class_name('text-muted').text
    assert(t == 'Sell your items from games and earn money!')

    ## earn money as seller by completing the order that was created by the first test user
    driver.get('http://localhost:3000/profile')
    # get currnet balance
    balance_prev = int(driver.find_element_by_class_name('balance-text').text)
    # go to sell page
    driver.get('http://localhost:3000/sell')
    # find row with first order created by the first test user
    ins = [e.text for e in driver.find_elements_by_class_name('email')]
    i = ins.index(f'test{ 1000 }@gmail.com')
    i+=1
    # get amount of money seller will earn for completing order
    payout = int(float(driver.find_element_by_id(i).find_element_by_class_name('payout').text))
    # click in complete
    form_complete_order = driver.find_element_by_id(i).find_element_by_tag_name('form')
    form_complete_order.submit()
    # check new balance
    driver.get('http://localhost:3000/profile')
    balance_after = int(driver.find_element_by_class_name('balance-text').text)
    assert(balance_prev + payout == balance_after)

    ## check if status of order of first test user changed
    driver.get('http://localhost:3000/logintestuser/1000')
    # get number of completed orders
    elems = driver.find_elements_by_class_name("order-status")
    completed_after = len([s for s in elems if s.text == 'completed'])
    assert(completed_prev + 1 == completed_after)

    ## Delete users
    r1 = requests.post('http://localhost:3000/admin/user/delete/?id=1000')
    r2 = requests.post('http://localhost:3000/admin/user/delete/?id=2000')
    assert(r1.status_code == 200)
    assert(r2.status_code == 200)

    # close driver
    driver.close()
