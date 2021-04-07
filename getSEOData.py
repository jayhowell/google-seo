from multiprocessing import Queue
from multiprocessing import Pool
from chromeBrowser import BrowserPool
import numpy as np

#create the browser pool to pull from
#get the list of words to
#run async job that pulls from the browser pool with the words from the list and pushes the data into a table
    #Write the data to the table as we go so we don't loose data if things crash   
    #Do these in pairs allinURL and allinTITLE together to make it easier
    #if either of the title or url fail, then we set a higher wait time for the browser instance in the browser pool.

def populateQueuefromFile(filename):
    q = Queue() #no max size for keywords
    file1 = open(filename, 'r')
    Lines = file1.readlines()
    # Strips the newline character
    for line in Lines:
        q.put(line.strip())
    return q

def populateArrayfromFile(filename):
    array = []
    file1 = open(filename, 'r')
    Lines = file1.readlines()
    # Strips the newline character
    for line in Lines:
        array.append(line.strip())
    return array

def workerfn(keyword):
    keeprunningallinurl = True
    keeprunningallintitle = True
    while keeprunningallintitle:
        with abrowserPool.get_resource() as browser:
            browser.printLog("Pulled resource out of pool")
            try:
                allintitle = browser.getAllInx(keyword)
                keeprunningallintitle = False #stop running this loop becuase we found a result
            except Exception as exception:
                browser.printLog("Threw exception in worker function getting allintitle for "+keyword)
                browser.printLog("Threw an Unknown Exception: {}".format(exception))
    while keeprunningallinurl:
        with abrowserPool.get_resource() as browser:
            browser.printLog("Pulled resource out of pool")
            try:
                allinurl = browser.getAllInx(keyword,x='url')
                keeprunningallinurl=False #stop running this loop becuase we found a result
            except Exception as exception:
                browser.printLog("Threw exception in worker function getting allinurl "+keyword)
                browser.printLog("Threw an Unknown Exception: {}".format(exception))
                
    results = [keyword,allintitle , allinurl,browser.proxy.host]
    print(results)
    return results


def getthtmlHeader():
    header = """
    <!DOCTYPE html>
<html>
<head>
    <style>
        table, th, td {
    border: 1px solid black;
}
th {
    cursor: pointer;
}
    </style>
    <script src="/scripts/snippet-javascript-console.min.js?v=1"></script>
</head>
<body>
    <table>
    <tr><th>KeyWords</th><th>Number In title</th><th>Number in URL</th><th>Score</th><th>Proxy Server</th></tr>
    """
    return header

def gethtmlFooter():
    footer = """
</table>
    <script type="text/javascript">
        const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;

const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
    v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
    )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

// do the work...
document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {
    const table = th.closest('table');
    Array.from(table.querySelectorAll('tr:nth-child(n+2)'))
        .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
        .forEach(tr => table.appendChild(tr) );
})));
    </script>
</body>
</html>
"""
    return footer
    
def keywordMessagePump():
    keywordsArray=populateArrayfromFile("keywords.txt")
    

    #proxyQueue=populateQueuefromFile("proxies.txt")
    #Start message pump
    #while not keywordsQueue.empty():
    #    item = keywordsQueue.get()
    #    print(item)    
    with Pool(processes=5) as pool:
        finalresults=pool.map(workerfn,keywordsArray,)

    html_file = open("output.html", "w")

    try:
        formulaResults=0
        html_file.write(getthtmlHeader())
        for each in finalresults:
            output_string = "<tr><td>{}</td><td><a href='https://www.google.com/search?q=allintitle:{}'>{}</a</td><td><a href='https://www.google.com/search?q=allinurl:{}'>{}</a></td><td>{}</td><td>{}</td></tr>".format(each[0],each[0],each[1],each[0],each[2],formulaResults,each[3]) #]proxyaddress)
            
            html_file.write(output_string)
        html_file.write(gethtmlFooter())
    except Exception as e:
        print("Exception: "+e)
    finally:
        html_file.close()

proxyArray = populateArrayfromFile("proxies.txt")
global abrowserPool #have to define a global so that we can access the pool in the callback
abrowserPool = BrowserPool(maxInstances=5,proxyArray=proxyArray)
keywordMessagePump()



    
