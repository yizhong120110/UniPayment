# -*- coding: utf-8 -*-
from xml.etree import ElementTree as et
from xml.dom import minidom
import re
from xml.parsers.expat import ExpatError

#xml_encoding = re.compile( '\<\?.*\?\>' )
xml_encoding = re.compile( "\<\!\[CDATA\[(.*?)\]\]\>" )                           
xml_parser_err = re.compile('.*?(?P<line>\d+),.*?(?P<col>\d+)')

def xmlroot( tagname , text=None , attrib={} , encoding='utf-8', **kwargs ):
    """
    将传入的内容生成一个ElementTree的根结点，并用encoding进行了解码转换
    传入参数
    tagname 根节点名称
    text 根节点对应的text
    attrib 根节点对应的属性
    encoding 传入内容的编码方式
    kwargs  根节点的补充内容
    """
    #if type( tagname ) == str:
    #    tagname = tagname.decode( encoding )
    
    d = {}
    for k, v in attrib.items():
        if type( k ) == str:
            k = k.decode( encoding )
        if type( v ) == str:
            v = v.decode( encoding )
        elif v is None:
            v = ''
        elif type( v ) != unicode:
            v = str( v )
        d[ k ] = v
    
    for k, v in kwargs.items():
        if type( v ) == str:
            v = v.decode( encoding )
        elif v is None:
            v = ''
        elif type( v ) != unicode:
            v = str( v )
        d[ k ] = v
    
    e = et.Element( tagname , d )
    if text:
        if type( text ) == str:
            text = text.decode( encoding )
        e.text = text
    return e

def xmlappend( parent, tagname, text=None, attrib={}, encoding='utf-8', **kwargs ):
    """
    将传入的内容生成一个ElementTree的结点，并作为parent的子节点，用encoding进行了解码转换
    传入内容的编码方式入参数
    parent 父节点名称
    tagname 子树根节点名称
    text 根节点对应的text
    attrib 根节点对应的属性
    encoding 传入内容的编码方式
    kwargs  根节点的补充内容
    """
    #if type( tagname ) == str:
    #    tagname = tagname.decode( encoding )
    
    d = {}
    for k, v in attrib.items():
        if type( k ) == str:
            #k = k.decode( encoding )
            pass
        if type( v ) == str:
            #v = v.decode( encoding )
            pass
        elif v is None:
            v = ''
        elif type( v ) != unicode:
            v = str( v )
        d[ k ] = v
    
    for k, v in kwargs.items():
        if type( v ) == str:
            #v = v.decode( encoding )
            pass
        elif v is None:
            v = ''
        elif type( v ) != unicode:
            v = str( v )
        d[ k ] = v
    
    e = et.SubElement( parent, tagname, d )
    if text:
        #if type( text ) == str:
        #    text = text.decode( encoding )
        e.text = text
    return e

def xmlout( ele , encoding = 'utf-8' , with_header = True , pretty = False ):
    """
    将ElementTree对象转换成xml报文输出
    参数列表
    ele ElementTree对象
    encoding 编码格式
    with_header 是否要加文件头（<?xml version='1.0' encoding='%s'?>\n）
    pretty 是否以xml的形式展现，否的话是一行输出没有xml的缩进等
    """
    s = et.tostring( ele , 'utf-8' )
    if pretty:
        reparsed = minidom.parseString( s )
        return reparsed.toprettyxml( indent="    " , encoding = encoding )
    
    # 将byte数据转换成str
    s = s.decode('utf-8')
    ret = s.split( '\n' , 1 )[-1]
    if with_header:
        buf = "<?xml version='1.0' encoding='%s'?>" % encoding + ret
    else:
        buf = ret
    buf = buf.encode( encoding )
    return buf

def xml( buf , encoding = 'utf-8' ):
    """读取xml报文，并返回根的elementtree对象
      该函数关注的是报文的编码转换
      参数列表：buf，报文内容,buf的数据类型是bytes
      encoding ：报文的编码格式
    """
    buf = buf.decode( encoding )
    g = xml_encoding.match(buf)
    if g:
        encode_old = g.group()
        buf = buf.replace(encode_old,"<?xml version='1.0' encoding='utf-8'?>")
    else:
        buf = "<?xml version='1.0' encoding='utf-8'?>\n" + buf
    try:
        return et.XML( buf )
    except ExpatError as e :
        m = xml_parser_err.match(e.args[0])
        if m:
            errdict = m.groupdict()
            raise  RuntimeError( '报文在第[%s]行第[%s]列出错，请检查此报文:\n%s' % ( errdict['line'], errdict['col'] ,e.args[0] ) )

def xmlread( e , path , attrs = None , encoding = 'utf-8' ):
    """读取指定的相对E节点的路径数据。
    参数列表:
    e 节点
    path 相对e节点的路径
    attrs 为列表或元组
      其中：None表示text
            其他字符串表示属性名称
    返回结果：
      属性内容。当只有一个属性时，仅返回一个值，不返回元组
      另外，当path会找到N个值时，返回所有节点对应的内容
    """ 
    #if type( path ) != 'unicode':
    #    path = path.decode( encoding )
    
    ll = e.findall( path )
    result = []
    for i in ll:
        if attrs is None:
            attrs = ( None , )
        if type( attrs ) not in ( list , tuple ):
            attrs = ( attrs , )
        r2 = []
        for a in attrs:
            if a is None:
                # 取Text属性
                r2.append( i.text.encode( encoding ) if i.text else '' )
            else:
                # 取属性
                r2.append( i.attrib.get( a , '' ).encode( encoding ) )
        
        result.append( r2[0] if len( r2 ) == 1 else r2 )
    if result:
        r = result[0] if len( result ) == 1 else result
        r = r.decode('utf8') if r else r
        return r

#返回所有具有相同标签的子
def xmlreadobj( e , path , encoding = 'utf-8' ):
    #if type( path ) != 'unicode':
    #    path = path.decode( encoding )
    ll = e.findall( path )
    return ll

if __name__ == '__main__':
#    fn = "9999999901020001_9999999912020001_17_810C028E88E835739BAAB694136B35FB.xml" # 文件名称
#    dir = "D:/20100925/" + fn
#    f= open(dir,'r')
#    buf = f.read()
#    buf = buf[buf.find('<'):]
#    root = xml( buf , 'utf8' )
#    print '>>>>>>>>>>>>>>>>>',xmlread(root,'Header/MessageClass'),xmlread(root,'Header/MessageType')
#    print '>>>>>>>>>>>>>>>>>>>>',root.tag ,xmlread(root,'Body','ContentType')
#    ll = xmlreadobj(root,'Body/Transaction')
#    for i in ll:
#        #在此处调用你写的通用函数
#        print i.tag,i.text
#        print xmlread(i,'TransId')

####    buf="""<CFX>
####        <HEAD>
####            <SRC>6001</SRC>
####            <DES>9999</DES>
####            <APP>财税</APP>
####        </HEAD>
####        <MSG>
####            <交易码  val="1104"/>
####            <纳税人编号  val="012345678901234567"/>
####            <税务机构  val="1"/>
####            <发起机构  val="6001"/>
####        </MSG>
####</CFX>
####"""
####    buf = """<szlr><input><trxcode>10001</trxcode></input></szlr>"""
####    
    ####buf = "<fk><header><successflag>1</successflag><desc>成功</desc></header><body><xyid>20130809120000admin</xyid><cgscdalx><dalx>1</dalx><dalx>2</dalx><dalx>3</dalx></cgscdalx></body></fk>"
####    #db_dic2 = unpack_upload( dbkk_buf )
####    #print ('>>>>>>>>>>>>>>dbkk_buf',db_dic2)
####    root = xml( buf , "gbk" )
####    #xyxx_dic = unpack_xyheader( root )
####    xyid = xmlread( root , "body/xyid" )           #协议ID
####    dalx = xmlread( root , "body/cgscdalx/dalx" )  #档案类型
####    print ('xyid>>>>>>>>>>',xyid)
####    print ('dalx>>>>>>>>>>',dalx)
####    trxcode = xmlread( root , "input/trxcode" ) # 交易码
####    print ('trxcode>>>>>>>>>>',type(trxcode))
####    #t =trxcode.decode('utf8')
####    print (type(trxcode),trxcode)
    # 打包测试
    
    ###### 组织报文
    #####r = xmlroot( "szlr" )
    ######写入报文体
    #####b = xmlappend( r , "output" )
    ###### 交易状态 00：成功 01：失败
    #####xmlappend( b , 'status', attrib={ 'val': '00' })
    ###### 交易结果 0000：成功 0001：失败
    #####xmlappend( b , 'retcode', attrib={ 'val': '0000' })
    ###### 响应信息
    #####buf = xmlout( r , encoding="gb18030" , with_header=True )
    #####print ('buf>>>>>>>>>>>>>',buf)
    buf = """<ROOT><HEAD TYPE="1" CODE="3059" ><STATUS>0</STATUS><ERRCODE>EGOV-1004</ERRCODE><MESSAGE>对帐完成，但有错误！ </MESSAGE></HEAD><BODY><DATA><DZSBWJM>304810420150710165745.txt</DZSBWJM></DATA></BODY></ROOT>"""
    root = xml( buf.encode(encoding="GBK") ,'gbk' )
    print ('r>>>>>>>>>>>>>',root)
