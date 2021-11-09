MYDIR=`dirname $0`
cp /etc/hadoop/conf/hdfs-site.xml $MYDIR/client_conf/
cp /etc/hadoop/conf/yarn-site.xml $MYDIR/client_conf/
cp /etc/hadoop/conf/core-site.xml $MYDIR/client_conf/
cp /etc/hadoop/conf/mapred-site.xml $MYDIR/client_conf/
cp /etc/hive/conf/hive-site.xml $MYDIR/client_conf/
cp /etc/hbase/conf/hbase-site.xml $MYDIR/client_conf/

echo "hadoop client configuration files are copied"