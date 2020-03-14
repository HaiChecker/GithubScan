import re


def payloadPatterns(patterns, content, url):
    result = {'url': url}
    hit = []
    # 判断是否存在Payload
    if len(patterns) > 0:

        for p in patterns:
            data = p['pattern'].findall(content)
            if len(data) > 0:
                payloadResult = []
                for pData in data:
                    payloadResult.append(pData)
                hit.append({p['id']: payloadResult})
    result['data'] = hit
    print(result)


a = """
    qx.defaule.mysql.jdbc.checkoutTimeout=30000
qx.defaule.mysql.jdbc.idleConnectionTestPeriod=30
qx.defaule.mysql.jdbc.initialPoolSize=10
qx.defaule.mysql.jdbc.maxIdleTime=30
qx.defaule.mysql.jdbc.maxPoolSize=100
qx.defaule.mysql.jdbc.minPoolSize=10
qx.defaule.mysql.jdbc.maxStatements=200

#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://dev.mysql.imfbp.com:3306/bj
qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://dev-test.mysql.imfbp.com:3306/boss_g?useUnicode=true&characterEncoding=utf-8
qx.defaule.mysql.jdbc.user=super
qx.defaule.mysql.jdbc.password=super@1

wangxiao.dbName=boss_g
wangxiao.exportPath=/Users/quanjianjun/work_folder/IdeaProjects/boss
wangxiao.tableNames=boss_theme
wangxiao.packageName=com.ifbp.boss
wangxiao.freemakerTemplatePath=/Users/quanjianjun/work_folder/IdeaProjects/platform-generator/template/freemaker/boss

checkoutTimeout=30000
idleConnectionTestPeriod=30
initialPoolSize=10
maxIdleTime=30

maxPoolSize=100
minPoolSize=10
maxStatements=200
qx.defaule.mysql.jdbc.driverClass=com.mysql.jdbc.Driver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://10.10.71.26:3306/rz
#qx.defaule.mysql.jdbc.user=rz
#qx.defaule.mysql.jdbc.password=rz

#qx.defaule.mysql.jdbc.driverClass=oracle.jdbc.driver.OracleDriver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:oracle:thin:@10.11.80.59:1521:orcl
#qx.defaule.mysql.jdbc.user=User1
#qx.defaule.mysql.jdbc.password=1

#qx.defaule.mysql.jdbc.driverClass=com.mysql.jdbc.Driver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://127.0.0.1/permit
#qx.defaule.mysql.jdbc.user=permit
#qx.defaule.mysql.jdbc.password=1234


#qx.defaule.mysql.jdbc.driverClass=com.mysql.jdbc.Driver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://127.0.0.1/permit
#qx.defaule.mysql.jdbc.user=permit
#qx.defaule.mysql.jdbc.password=1234

#qx.defaule.mysql.jdbc.driverClass=com.mysql.jdbc.Driver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://localhost:3306/test?useUnicode=true&amp;characterEncoding=UTF8
#qx.defaule.mysql.jdbc.user=root
#qx.defaule.mysql.jdbc.password=123456

#qx.defaule.mysql.jdbc.driverClass=com.mysql.jdbc.Driver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://192.168.1.168:3306/plat_permit?useUnicode=true&amp;characterEncoding=UTF8
#qx.defaule.mysql.jdbc.user=root
#qx.defaule.mysql.jdbc.password=123456

#qx.defaule.mysql.jdbc.driverClass=com.mysql.jdbc.Driver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://127.0.0.1:3306/platform?useUnicode=true&amp;characterEncoding=UTF8
#qx.defaule.mysql.jdbc.user=root
#qx.defaule.mysql.jdbc.password=123456

#success.alleviation.jdbc.driver=com.mysql.jdbc.Driver
#success.alleviation.jdbc.url=jdbc:mysql://192.168.1.189:3306/platform?useUnicode=true&amp;characterEncoding=UTF8
#success.alleviation.jdbc.username=root
#success.alleviation.jdbc.password=123456

#qx.defaule.mysql.jdbc.driverClass=oracle.jdbc.driver.OracleDriver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:oracle:thin:@192.168.1.218:1521:jdlk1
#qx.defaule.mysql.jdbc.user=jdlk1
#qx.defaule.mysql.jdbc.password=jdlk1

#qx.defaule.mysql.jdbc.driverClass=oracle.jdbc.driver.OracleDriver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:oracle:thin:@192.168.1.225:1521:skss
#qx.defaule.mysql.jdbc.user=tyzj
#qx.defaule.mysql.jdbc.password=skss

#qx.defaule.mysql.jdbc.driverClass=com.mysql.jdbc.Driver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://127.0.0.1:3306/permit?useUnicode=true&amp;characterEncoding=UTF8
#qx.defaule.mysql.jdbc.user=root
#qx.defaule.mysql.jdbc.password=123456

#qx.defaule.mysql.jdbc.driverClass=com.mysql.jdbc.Driver
#qx.defaule.mysql.jdbc.jdbcUrl=jdbc:mysql://192.168.183.128:3306/dongao_test?useUnicode=true&amp;characterEncoding=UTF8
#qx.defaule.mysql.jdbc.user=dong_test
#qx.defaule.mysql.jdbc.password=123

#user=test
#password=1
##jdbcUrl=jdbc:oracle:thin:@//10.10.65.168:1521/orcl
#jdbcUrl=jdbc:oracle:thin:@//localhost:1521/orcl
#driverClass=oracle.jdbc.OracleDriver
"""

r = re.compile(r'(mysql:\/\/[\w\-]+\.[\w\-]+[\w\-.,@?^=%&:\/~+#]*[\w\-@?^=%&\/~+#])', re.S)
d = r.findall(a)
print(d)
