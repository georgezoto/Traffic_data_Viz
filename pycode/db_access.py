"""
Date: Fri Jun 13 22:12:05 2014
@author: Kevin Lu
@email: kevinlu@vt.edu

Description: Database method assembly for traffic visualization
"""

import pyodbc
import xml.etree.cElementTree as ET
import datetime
import os

# Hard coding area
CorridorFile = 'corridors.txt'
db_setting_path = 'dbsettings.json'
folder = os.path.dirname(os.path.abspath(__file__))
CorridorFile = os.path.join(folder, CorridorFile)
db_setting_path = os.path.join(folder, db_setting_path)
# -----------------

def load_dbsetting_file(fpath):
    """
    return db settings DBServer, DBname, UID, PWD, TABLENAME
    """
    f = open(fpath, 'r')
    import json
    dct = json.load(f)
    f.close()
    return dct["DBServer"], dct["DBName"], dct["UID"], dct["PWD"], dct["TABLENAME"]

def load_corridors():
    cor_data = {}
    f = open(CorridorFile,'r')
    lines = f.readlines()
    for i, line in enumerate(lines):
        l = line.split(':')
        cid = l[0].strip()
        name = l[1].strip()
        acisa_range = l[2].strip()
        intersections = [t.strip() for t in l[3].split(',')]
        cor_data[cid] = {'name': name, 'acisa_range': acisa_range, 'intersections': intersections}
    f.close()    
    return cor_data

def query_by_corridor_group(corridor_id, start_date, end_date, output_format='csv'):
    """
    for generating "New Zealand Earthquakes" plot    
    http://bl.ocks.org/d3noob/4425979
    
    returns the aggregated value

    corridor_id:
        1:NY AVE
        2:CT AVE
        3:14TH ST
        4:Constitution AVE
        5:Reservoir - MacArthur
        6:H st - Bening Rd        

    start_date, end_date:
        YYYY-MM-DD        

    output_format:
        'csv', 'xml'
    """
    # get corridor ACISA list
    cor_data = load_corridors()
    corr_acisas = ','.join('\'' + t + '\'' for t in cor_data[str(corridor_id)]['intersections'])
        
    # query data
    DBserver, DBname, UID, PWD, tblname = load_dbsetting_file(db_setting_path)
    connStr = (r'DRIVER={SQL Server};SERVER=' +
            DBserver + ';DATABASE=' + DBname + ';' +
            'UID=' + UID + ';PWD=' + PWD)
        
    conn = pyodbc.connect(connStr)    

#    query = "SELECT data_datetime, ACISA, laneDir, VolSum, avg_speed FROM %s WHERE ACISA IN (%s) " % (tblname, corr_acisas) \
#            + "AND data_datetime between \'%s\' and \'%s\' ORDER BY ACISA, data_datetime ASC" % (start_date, end_date)
    
    query = "SELECT data_datetime, laneDir, sum(VolSum), avg(avg_speed) FROM %s WHERE ACISA IN (%s) " % (tblname, corr_acisas) \
            + "AND data_datetime between \'%s\' and \'%s\' GROUP BY laneDir, data_datetime ORDER BY laneDir, data_datetime ASC" % (start_date, end_date)        

    dbCursor = conn.cursor()
    dbCursor.execute(query)
    
    info = {}
    
    for row in dbCursor:
#        (dt, acisa, lanedr, vol, avgspd) = tuple(row[0:6])
#        print  dt, acisa, lanedr, vol, avgspd
        (dt, lanedr, vol, avgspd) = tuple(row[0:4])
        if(not info.has_key(lanedr)):
            info[lanedr] = []
        info[lanedr].append({'datetime': dt,'speed': avgspd, 'vol': vol})
#        print  dt, lanedr, vol, avgspd
        
    if(output_format == 'xml'):
        # construct XML
        root = ET.Element("items")
        for k, v in info.items():
            lanedr = ET.SubElement(root, "lanedr")
            lanedr.set('direction', k.strip())
            for v0 in v:
                item = ET.SubElement(lanedr, "item")
                item.set("datetime", v0['datetime'].strftime("%Y-%m-%d %H:%M:%S"))
                item.set("speed", str(v0['speed']))
                item.set("vol", str(v0['vol']))
           
        tree = ET.ElementTree(root)
    #    tree.write("test.xml") # write to a temporary file
        return ET.dump(tree) # return an XML string
        
    elif(output_format == 'csv'):        
        # construct csv
        text = ["week_year,day_time,speed,vol,lanedr"]
        for k, v in info.items():            
            kk = k.strip()
            for v0 in v:
                wday = datetime.datetime(1900,1,7, v0['datetime'].hour, v0['datetime'].minute, v0['datetime'].second) + datetime.timedelta( (v0['datetime'].weekday() + 1) % 7  ,0)
                text.append("%s,%s,%s,%s,%s" % (v0['datetime'].strftime("%Y-%m-%d"), wday.strftime("%Y-%m-%d %H:%M:%S"), str(v0['speed']), str(v0['vol']), kk))
        outtext = '\n'.join(t for t in text)
        return outtext


def query_by_acisa(acisa, start_date, end_date, output_format='csv'):
    # query data
    DBserver, DBname, UID, PWD, tblname = load_dbsetting_file(db_setting_path)
    connStr = ( r'DRIVER={SQL Server};SERVER=' +
            DBserver + ';DATABASE=' + DBname + ';' +
            'UID=' + UID + ';PWD=' + PWD)

    conn = pyodbc.connect(connStr)

#    query = "SELECT data_datetime, ACISA, laneDir, VolSum, avg_speed FROM %s WHERE ACISA IN (%s) " % (tblname, corr_acisas) \
#            + "AND data_datetime between \'%s\' and \'%s\' ORDER BY ACISA, data_datetime ASC" % (start_date, end_date)

    query = "SELECT data_datetime, laneDir, sum(VolSum), avg(avg_speed) FROM %s WHERE ACISA IN (%s) " % (tblname, acisa) \
            + "AND data_datetime between \'%s\' and \'%s\' GROUP BY laneDir, data_datetime ORDER BY laneDir, data_datetime ASC" % (start_date, end_date)
#    print query

    dbCursor = conn.cursor()
    dbCursor.execute(query)

    info = {}

    for row in dbCursor:
#        (dt, acisa, lanedr, vol, avgspd) = tuple(row[0:6])
#        print  dt, acisa, lanedr, vol, avgspd
        (dt, lanedr, vol, avgspd) = tuple(row[0:4])
        if(not info.has_key(lanedr)):
            info[lanedr] = []
        info[lanedr].append({'datetime': dt,'speed': avgspd, 'vol': vol})
#        print  dt, lanedr, vol, avgspd

    if(output_format == 'xml'):
        # construct XML
        root = ET.Element("items")
        for k, v in info.items():
            lanedr = ET.SubElement(root, "lanedr")
            lanedr.set('direction', k.strip())
            for v0 in v:
                item = ET.SubElement(lanedr, "item")
                item.set("datetime", v0['datetime'].strftime("%Y-%m-%d %H:%M:%S"))
                item.set("speed", str(v0['speed']))
                item.set("vol", str(v0['vol']))

        tree = ET.ElementTree(root)
    #    tree.write("test.xml") # write to a temporary file
        return ET.dump(tree) # return an XML string

    elif(output_format == 'csv'):
        # construct csv
        text = ["week_year,day_time,speed,vol,lanedr"]
        for k, v in info.items():
            kk = k.strip()
            for v0 in v:
                wday = datetime.datetime(1900,1,7, v0['datetime'].hour, v0['datetime'].minute, v0['datetime'].second) + datetime.timedelta( (v0['datetime'].weekday() + 1) % 7  ,0)
                text.append("%s,%s,%s,%s,%s" % (v0['datetime'].strftime("%Y-%m-%d"), wday.strftime("%Y-%m-%d %H:%M:%S"), str(v0['speed']), str(v0['vol']), kk))
        outtext = '\n'.join(t for t in text)
        return outtext

# testing command
#print query_by_corridor_group('1', '2013-10-01', '2013-10-31')
# print query_by_acisa('2135', '2013-10-01', '2013-10-31')
