# append Hive libraries from cluster
function enableMRHiveLibs {
    INCLUDE=(hive-hcatalog-core- hive-metastore- hive-common- hive-exec- libfb303)
    IFS=':' read -a HCPA <<< $(hcat -classpath)
    for cp in "${HCPA[@]}"
    do
        [ "$cp" ] || continue
        [ -f "$cp" ] || continue
        name=$(basename "$cp")
        for inc in "${INCLUDE[@]}"
        do
            if [[ $name = $inc* ]]
            then
                HIVE_CLUSTER_CP+=":$cp"
            fi
         done
    done
    if [[ $HIVE_CLUSTER_CP == :* ]]
        then HIVE_CLUSTER_CP=${HIVE_CLUSTER_CP:1}
    fi
}

function confFileExists {
	if [[ -f "$MYDIR/client_conf/core-site.xml" && -f "$MYDIR/client_conf/yarn-site.xml" && -f "$MYDIR/client_conf/hive-site.xml" && -f "$MYDIR/client_conf/hdfs-site.xml" && -f "$MYDIR/client_conf/hbase-site.xml" ]]; then
		return 0
	else
		return 1
	fi
}
	
function checkHadoopClientConfig {
	if ! confFileExists; then
		echo "$MYDIR/client_conf folder does not contain needed hadoop configuration. 
			Attempting to copy the files from default locations:
			  - /etc/hadoop/conf 
			  - /etc/hive/conf/ 
			  - /etc/hbase/conf"
		if [ -d "/etc/hadoop/conf/" ]; then
			cp /etc/hadoop/conf/hdfs-site.xml $MYDIR/client_conf/
			cp /etc/hadoop/conf/yarn-site.xml $MYDIR/client_conf/
			cp /etc/hadoop/conf/core-site.xml $MYDIR/client_conf/
			cp /etc/hadoop/conf/mapred-site.xml $MYDIR/client_conf/
			cp /etc/hive/conf/hive-site.xml $MYDIR/client_conf/
			cp /etc/hbase/conf/hbase-site.xml $MYDIR/client_conf/
			if ! confFileExists; then
				echo "Files were not properly copied"
				echo "Please copy hadoop client configuration to the client_conf folder manually"
				exit 1
			else
				echo "Finished"
			fi
		else
			echo "/etc/hadoop/conf/ does not exist!!!"
			echo "Please copy hadoop client configuration to the client_conf folder manually"
			exit 1
		fi
	fi
}

function findSparkHome {
	if [ -d "/opt/cloudera/parcels/SPARK2/lib/spark2/" ]; then
		SPARK_HOME="/opt/cloudera/parcels/SPARK2/lib/spark2/"
		if [[ "$SPARK_DIST_CLASSPATH" = "" && "$ENABLE_SPARK_DIST_CLASSPATH" = "" ]]; then
			echo "Hadoop cluster was automatically identified as Cloudera. Setting SPARK_DIST_CLASSPATH"
			export SPARK_DIST_CLASSPATH=`hadoop classpath`
		fi
	elif [ -d "/usr/hdp/current/spark2-client/" ]; then
		SPARK_HOME="/usr/hdp/current/spark2-client/"
	elif [ -d "/usr/hdp/current/spark2-client/" ]; then
		SPARK_HOME="/usr/lib/spark/"
	else 
		echo "SPARK_HOME IS NOT FOUND. Please Specify env.SPARK_HOME manually in hadoop.properties file"
		exit 1
    fi
}

function validateSparkProperties {
	file="$MYDIR/spark.properties"
	while IFS= read -r line
	do
			if [[ "$line" == spark.yarn.historyServer.address=http?* ]]; then
					found_history_address=1
			fi
	
			if [[ "$line" == spark.eventLog.dir=hdfs?* ]]; then
					found_event_log=1
			fi
	
			if [[ "$line" == spark.sql.hive.metastore.jars=?* ]]; then
					found_hive_jars=1
			fi
	
	done <"$file"
	
	if ! [ "$found_history_address" = 1 ]; then
			echo "spark.yarn.historyServer.address variable is not set in [DQC_HOME]/server/executor/spark.properties file."
			echo "Please specify the URL for YARN History Server."
			echo "Exiting..."
			exit 1
	fi
	if ! [ "$found_event_log" = 1 ]; then
			echo "spark.eventLog.dir variable is not set in [DQC_HOME]/server/executor/spark.properties file."
			echo "Please specify the location of Spark logs."
			echo "Exiting..."
			exit 1
	fi
	if ! [ "$found_hive_jars" = 1 ]; then
			echo "spark.sql.hive.metastore.jars variable is not set in [DQC_HOME]/server/executor/spark.properties file."
			echo "Please specify the jars location."
			echo "Exiting..."
			exit 1
	fi
}

function enableSparkHiveLibsFull {
    INCLUDE=(hive-hcatalog-core- hive-metastore- hive-common- hive-exec- libfb303)
    IFS=':' read -a HCPA <<< $(hcat -classpath)
    for cp in "${HCPA[@]}"
    do
        [ "$cp" ] || continue
        [ -f "$cp" ] || continue
        name=$(basename "$cp")
        for inc in "${INCLUDE[@]}"
        do
            if [[ $name = $inc* ]]
            then
                HIVE_CLUSTER_CP+=":$cp"
            fi
        done
    done
    if [[ $HIVE_CLUSTER_CP == :* ]]
    	then HIVE_CLUSTER_CP=${HIVE_CLUSTER_CP:1}
    fi
}

# append HBase libraries from cluster
function enableHBaseLibs {
    INCLUDE=(hbase-client- hbase-common- hbase-hadoop-compat- hbase-hadoop2-compat- hbase-protocol- hbase-server- htrace-)
    IFS=':' read -a HCPA <<< $(hbase classpath)
    for cp in "${HCPA[@]}"
    do
        [ "$cp" ] || continue
        [ -f "$cp" ] || continue
        name=$(basename "$cp")
        for inc in "${INCLUDE[@]}"
        do
            if [[ $name = $inc* ]]
            then
                HBASE_CLUSTER_CP+=":$cp"
            fi
        done
    done
    if [[ $HBASE_CLUSTER_CP == :* ]]
        then HBASE_CLUSTER_CP=${HBASE_CLUSTER_CP:1}
    fi
}

# append Hadoop libraries from cluster to local classpath
function enableLocalHadoopClasspath {
    IFS=':' read -a HCPA <<< $(hadoop classpath)
    for dir in "${HCPA[@]}"
    do
        [ "$dir" ] || continue
        for entry in "$dir"
        do
            if [[ $entry == *'/*' ]]
            then
                    LOCAL_CP+=":$entry"
            fi

            #[ -f "$entry" ] || continue
            #fname=$(basename "$entry")
            #for inc in "${INCLUDE[@]}"
            #do
            #        if [[ $fname = *$inc ]]
            #        then
            #                LOCAL_CP+=":$entry"
            #        fi
            #done
        done
    done
    LOCAL_CP=${LOCAL_CP:1}
}
