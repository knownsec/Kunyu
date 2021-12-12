#!/usr/bin/env python
# encoding: utf-8
"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: createmap.py
@Time: 2021/12/6 8:55
"""


def create_data_map(data, data_map_name):
    html = str(data_map_name)
    body = '{width: 100%;height: 100%;overflow: hidden;margin:0;font-family:"微软雅黑";}'
    f = open(html, 'w', encoding='utf-8')
    message = """
    <!DOCTYPE html> 
    <html> 
        <head> 
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
        <link rel="shortcut icon" href="https://gitee.com/gui-yunyou/kunyu_ico/raw/master/favicon.ico" type="image/x-icon">
        <style type="text/css"> 
            body, html,#allmap%s
            .BMap_cpyCtrl {
                display: none !important;
            }
            .anchorBL {
                display: none !important;
            }
        </style> 
        <script type="text/javascript" 
            src="http://api.map.baidu.com/api?v=2.0&ak=WjqIEPES5kODPcbszyt29MhBX4FC2xa0">
        </script> 
        <title>Kunyu（坤舆）资产分布图</title> 
        </head> 
        <body> 
        <div id="allmap"></div> 
        </body> 
    </html> 
    
    <script type="text/javascript">
        var points = %s;
        function addMarker(points) {
            for(var i=0, pointsLen = points.length; i<pointsLen; i++) {
                var point = new BMap.Point(points[i].lng, points[i].lat);
                var marker = new BMap.Marker(point);
                map.addOverlay(marker);
                var thePoint = points[i];
                //Listen for mouse click events
                marker.addEventListener("click",
                function() {
                    showInfo(this,thePoint);
                });
            }
        }
        
        //Set the description of the marker
        function showInfo(thisMarker,point) {
            var sContent = 
                '<ul style="margin:0 0 5px 0;padding:0.2em 0">'  
                +'<li style="line-height: 35px;font-family:"楷体";font-size: 30px;">'  
                +'<span style="width: 50px;display: inline-block;">IP:</span>' + point.ip + '</li>'  
                +'<li style="line-height: 35px;font-family:"楷体";font-size: 30px;">'  
                +'<span style="width: 50px;display: inline-block;"> 纬度:</span>' +point.lat +
                '<br><span style="width: 50px;display: inline-block;"> 经度:</span>' + point.lng +'</li>'  
                +'</ul>';
            var infoWindow = new BMap.InfoWindow(sContent);
            
            thisMarker.openInfoWindow(infoWindow);
            }
            
            //Generate the map and set
            var map = new BMap.Map("allmap");
            map.centerAndZoom(new BMap.Point(116.418261,39.921984), 5);
            map.addControl(new BMap.MapTypeControl({mapTypes: [BMAP_NORMAL_MAP,BMAP_SATELLITE_MAP,BMAP_HYBRID_MAP]}));
            map.addControl(new BMap.ScaleControl({anchor: BMAP_ANCHOR_TOP_LEFT}));
            map.addControl(new BMap.OverviewMapControl());
            map.addControl(new BMap.OverviewMapControl({isOpen:true, anchor: BMAP_ANCHOR_BOTTOM_RIGHT}))
            map.addControl(new BMap.NavigationControl());
            map.enableScrollWheelZoom(true);     
            addMarker(points);
    </script>
    
    """ % (body, data)
    f.write(message)
    f.close()
