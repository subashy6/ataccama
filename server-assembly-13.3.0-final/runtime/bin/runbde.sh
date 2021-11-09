#!/bin/bash

case ${OSTYPE//[0-9.]/} in
	darwin)
		OS=darwin
		;;
	cygwin*)
		OS=windows
		;;
	msys*)
		OS=windows
		;;
	linux*)
		OS=linux
		;;
esac

function errecho {
	>&2 echo "$@"
}

function verbecho {
	if [ $VERBOSE -gt 0 ]; then
		echo "$@"
	fi
}

function verbrun {
	verbecho "$@"
	"$@"
}

SELF="`basename $0`"
SELF_DIR="`dirname $0`"

function usage {
	cat <<END
$SELF [-d | --debug[=PORT/SUSPEND]] [-r | --runtime DQC_HOME] [-p | --prop[ertie]s PROP_FILE] [-v | --verbose] [-h | --help]
	[--cp | --classpath PATH] [--hcp | --hadoop-cp | --hadoop-classpath]
	[--local | --mr | ( --spark [--s[park-]home SPARK_HOME] )] [--executor]
	(--dqc | --bde | --dqd | --ewf)
	[--] ARGS

DESCRIPTION:
	This script starts various products (see PRODUCT SELECTION section below) in various modes.
	All products can run locally (L), some of them can be run in Map-Reduce (MR) and in Spark (S).
	Also, some products can use Ataccama Remote Executor.

OPTIONS:
	-d, --debug[=PORT/SUSPEND]
		Enables remote debugging on port PORT (default 8787) and sets suspend to SUSPEND (default n).

	-r DQC_HOME, --runtime DQC_HOME
		Sets the DQC_HOME manually; use this if you want to override the env. variable, or if it could not have been found automatically.

	-v, --verbose
		Prints out which values are used while running the script.

	-h, --help
		Prints this documentation and ends.

CLASSPATH:
	--cp PATH, --classpath PATH
		Adds jars to the classpath.
		
	--hcp, --hadoop-cp, --hadoop-classpath
		Adds the hadoop classpath to the classpath, which is useful for Map-Reduce.
		This option uses the command hadoop which must be available.

MODES:
	--local
		Runs locally (default).
		
	-p PROP_FILE, --props PROP_FILE, --properties PROP_FILE
		Sets the location of the properties file which configures the access to a cluster in case of the MR or Spark mode.

	--mr
		Runs on cluster using Map-Reduce.
		
	--shome SPARK_HOME, --spark-home SPARK_HOME
		Sets the environmental variable SPARK_HOME which is needed for Spark mode.

	--spark
		Runs on cluster using Spark.
		If executor is not used, the application is internally submited by the spark-submit script from the provided Spark distribution, see SPARK_HOME.
		The user must specify the spark distribution location either via --spark-home, or the environmental variable SPARK_HOME.
		
	--executor
		Run via Ataccama Remote Executor. It works in combination with --mr and --spark modes.

PRODUCT SELECTION:
	--dqc, --bde
		(L, MR, S) Processes a DQC plan. The product --bde is nothing more than an alias to --dqc.

	--dqd
		(L, S) Processes a system of a DQD project or deploys a new configuration into datamart.

	--ewf
		(L) Processes an EWF workflow.
	
	--custom CLASS
		(L, MR, S) Starts the given CLASS in the given mode.

ENVIRONMENTAL VARIABLES:
	The script can be controlled by several variables; they are sorted in order of desirability to be used.

	DQC_HOME:
		The directory of the DQC runtime; it must contain the subdirectory "lib".
		If using a runtime from a build, DQC_HOME is found automatically.
		It can also be set by the option --runtime (-r).

	JAVA_HOME
		Specifies which java is going to be used.

	CLASSPATH:
		The additional classpath which is passed to java as a -cp argument.
		You can also use the --cp option for this.

	JAVA_OPTS:
		Additional options which are passed to java, such as setting maximal memory.
		Note that JAVA_OPTS must not contain -cp nor -classpath; they must be set in other ways.

	PROP_FILE:
		The properties file specifies where and how processing in Map-Reduce and Spark mode is going to be processed.
		It is usually set by the option --properties (-p).

	SPARK_HOME:
		The directory which contains the spark distribution.
		If a Spark distribution is located in DQC_HOME/lib/hadoop/ and is called "spark-*", it is found automatically.
		It can be set by the option --spark-home (--shome).
END
}

function addToClasspath {
	while [ $# -gt 0 ]; do
		if [ "$OS" = "windows" ]; then
			CLASSPATH="$CLASSPATH${CLASSPATH+;}$1"
		else
			CLASSPATH="$CLASSPATH${CLASSPATH+:}$1"
		fi
		shift
	done
}

function findGlobFirst {
	glob="$1"
	shift
	found="`find "$@" -iname "$glob" 2>/dev/null | head -n 1`"
	if [ -z "$found" ]; then
		errecho "Failed to find $glob in $@"
		exit 1
	fi
	echo "$found"
}

function addHadoopClasspath {
	if hadoop version >/dev/null 2>&1; then
		addToClasspath "`hadoop classpath`"
		verbecho "Hadoop JARs were added to the classpath."
		true
	else
		false
	fi
}

SHORT="+d::r:p:vh"
LONG_GENERAL="debug::,runtime:,props:,properties:,verbose,help"
LONG_CP="classpath:,cp:,hadoop-classpath,hadoop-cp,hcp"
LONG_MODES="local,mr,spark,shome:,spark-home:,executor"
LONG_PRODUCTS="dqc,dqd,ewf,custom:"
LONG="$LONG_GENERAL,$LONG_CP,$LONG_MODES,$LONG_PRODUCTS"

ARGS=$(getopt -a -o "$SHORT" -l "$LONG" -n "$SELF" -- "$@")

# bad arguments
if [ $? -ne 0 ]; then
	usage
	exit 1
fi

# set the unmatched arguments into $1, $2, ...
eval set -- "$ARGS"

# default mode
MODE="local"
VERBOSE=0
EXECUTOR=0
unset CLASS
unset PRODUCT

while true; do
	case "$1" in
		-d|--debug)
			DOPTS="${2}n8787"
			DPORT=`echo $DOPTS | grep -oE "[0-9]+" | head -1`
			DSUSPEND=`echo $DOPTS | grep -oE "[ny]" | head -1`

			JAVA_OPTS="$JAVA_OPTS -agentlib:jdwp=transport=dt_socket,server=y,address=$DPORT,suspend=$DSUSPEND"
			shift 2
		;;
		-r|--runtime)
			if which cygpath >/dev/null 2>&1; then
				DQC_HOME="`cygpath.exe -m -a "$2"`"
			else
				DQC_HOME="`readlink -f "$2"`"
			fi
			shift 2
		;;
		-p|--props|--properties)
			if which cygpath >/dev/null 2>&1; then
				export PROP_FILE="`cygpath.exe -m -a "$2"`"
			else
				export PROP_FILE="`readlink -f "$2"`"
			fi
			shift 2
		;;
		-h|--help)
			usage
			exit
		;;
		-v|--verbose)
			VERBOSE=1
			shift
		;;
		
		--cp|--classpath)
			addToClasspath "$2"
			shift 2
		;;
		--hcp|--hadoop-cp|--hadoop-classpath)
			if ! addHadoopClasspath; then
				errecho "The hadoop command is not available; set the hadoop classpath manually by option --cp, or in a properties file."
			fi
			shift
		;;

		--local)
			MODE="local"
			shift
		;;
		--mr)
			MODE="mr"
			shift
		;;
		--spark)
			MODE="spark"
			shift
		;;
		--shome|--spark-home)
			SPARK_HOME="$2"
			shift 2
		;;
		--executor)
			EXECUTOR=1
			shift
		;;
		
		--)
			shift
			break
		;;

		--dqc|--bde)
			PRODUCT="dqc"
			shift
		;;
		--dqd)
			PRODUCT="dqd"
			shift
		;;
		--ewf)
			PRODUCT="ewf"
			shift
		;;
		--custom)
			PRODUCT="custom"
			CLASS="$2"
			shift 2
		;;
		
		*)
			errecho "Found an unknown option $1"
			exit 1
		;;
	esac
done

function testHome {
	stat "$1/lib/"cif[.-]commons*.jar >/dev/null 2>&1
}

function checkHome {
	if [ -z "$DQC_HOME" ]; then
		_DQC_HOME=`readlink -f "$SELF_DIR/.."`
		if testHome "$_DQC_HOME"; then
			if which cygpath >/dev/null 2>&1; then
				DQC_HOME="`cygpath.exe -m -a "$_DQC_HOME"`"
			else
				DQC_HOME="`readlink -f "$_DQC_HOME"`"
			fi
			verbecho "Found DQC_HOME in $DQC_HOME, running with a build runtime."
		else
			errecho "DQC_HOME is unset; you must either:"
			errecho "	use the option --runtime (-r),"
			errecho "	or set the environmental variable DQC_HOME."
			exit 1
		fi
	fi
	if ! testHome "$DQC_HOME"; then
		errecho "DQC_HOME (${DQC_HOME}) is set to a wrong location."
		exit 1
	fi
	export DQC_HOME
	verbecho "Using DQC_HOME: $DQC_HOME"
}

function checkJava {
	# set JAVA_EXE
	if [ -z "$JAVA_HOME" ]; then
		# JAVA_HOME is not set, use the default java
		if ! which java >/dev/null 2>&1; then
			errecho "No Java found; set the environmental variable JAVA_HOME manually."
			exit 1
		else
			JAVA_EXE="`which java`"
		fi
	else
		# normalize JAVA_HOME
		if [ ! -d "$JAVA_HOME" ]; then
			errecho "JAVA_HOME ($JAVA_HOME) does not point to a directory."
			exit 1
		fi

		if which cygpath >/dev/null 2>&1; then
			JAVA_HOME="`cygpath.exe -m -a "$JAVA_HOME"`"
		else
			JAVA_HOME="`readlink -f "$JAVA_HOME"`"
		fi
		export JAVA_HOME

		# use Java from JAVA_HOME
		JAVA_EXE="$JAVA_HOME/bin/java"
		if [ \( ! -f "$JAVA_EXE" \) -o \( ! -x "$JAVA_EXE" \) ]; then
			errecho "JAVA_HOME (${JAVA_HOME}) is set to a wrong location."
			exit 1
		fi
	fi
	
	if ! "$JAVA_EXE" -version 2>&1 >/dev/null | grep -o '"1\.8' >/dev/null; then
		verbecho "Only Java version 1.8 is supported, using a potentially unsupported version."
	fi

	verbecho "Using JAVA_HOME: ${JAVA_HOME-unset}"
	verbecho "Using JAVA: $JAVA_EXE"
	verbecho "Using CLASSPATH: ${CLASSPATH-unset}"
}

function checkProps {
	if [ -z "$PROP_FILE" ]; then
		errecho "The properties file must be specified."
		exit 1
	fi

	# test properties file
	if [ ! -f "$PROP_FILE" ]; then
		errecho "The property file ($PROP_FILE) does not exist."
		exit 1
	fi

	verbecho "Using PROP_FILE: $PROP_FILE"
}

function testSpark {
	stat "$1/bin/spark-submit" >/dev/null 2>&1
}

function checkSpark {
	if [ -z "$SPARK_HOME" ]; then
		for _SPARK_HOME in "$DQC_HOME/lib/hadoop/spark"* "$DQC_HOME/../spark"* "$DQC_HOME/spark"* "$DQC_HOME/lib/spark"*; do
			if testSpark "$_SPARK_HOME"; then
				SPARK_HOME="$_SPARK_HOME"
				break
			fi
		done
		
		if [ -z "$SPARK_HOME" ]; then
			errecho "SPARK_HOME is unset; set the Spark distribution location either:"
			errecho "	using option --spark-home (--shome),"
			errecho "	or by env. variable SPARK_HOME,"
			errecho "	or put it into $DQC_HOME/lib/hadoop/ as a directory called \"spark-*\"."
			exit 1
		else
			verbecho "Found a Spark distribution in $SPARK_HOME"
		fi
	else
		if which cygpath >/dev/null 2>&1; then
			SPARK_HOME="`cygpath.exe -m -a "$SPARK_HOME"`"
		else
			SPARK_HOME="`readlink -f "$SPARK_HOME"`"
		fi
	fi
	
	if ! testSpark "$SPARK_HOME"; then
		errecho "The spark distribution ($SPARK_HOME) is invalid."
		exit 1
	fi
	verbecho "Using SPARK_HOME: $SPARK_HOME"
	export SPARK_HOME
}

checkHome
checkJava
if [ "$MODE" = "mr" -o "$MODE" = "spark" ]; then
	checkProps
fi
if [ "$MODE" = "local" -a "$EXECUTOR" = 1 ]; then
	checkProps
fi
if [ "$MODE" = "spark" -a "$EXECUTOR" = 0 ]; then
	checkSpark
fi

if [ -z "$PRODUCT" ]; then
	errecho "No product was specified; use either --dqc, --dqd, --ewf, or --custom CLASS."
	exit 1
else
	case "$PRODUCT-$EXECUTOR-$MODE" in
		dqc-0-local)
			CLASS="com.ataccama.dqc.processor.bin.CifProcessor"
		;;
		dqc-1-local)
			CLASS="com.ataccama.dqc.hadoop.plan.GatewayPlanMain"
		;;
		dqc-0-mr)
			CLASS="com.ataccama.dqc.hadoop.plan.PlanMain"
		;;
		dqc-1-mr)
			CLASS="com.ataccama.dqc.hadoop.plan.GatewayPlanMain"
		;;
		dqc-0-spark)
			CLASS="com.ataccama.dqc.spark.launcher.SparkPlanLauncher"
		;;
		dqc-1-spark)
			CLASS="com.ataccama.dqc.hadoop.plan.GatewayPlanMain"
		;;
		dqd-0-local)
			CLASS="com.ataccama.dqd.engine.DqdProcessor"
		;;
		dqd-0-spark)
			CLASS="com.ataccama.dqd.spark.DqdSparkLauncher"
		;;
		ewf-0-local)
			CLASS="com.ataccama.adt.runtime.EwfProcessor"
		;;
		custom-*)
			# do nothing CLASS has been set
		;;
		*)
			errecho "The combination of the product $PRODUCT and the mode $MODE is not supported."
			exit 1
		;;
	esac
fi

verbecho "Using MAIN: $CLASS"

case "$MODE":"$EXECUTOR" in
	local:0)
		addToClasspath "` findGlobFirst "cif[.-]bootstrap*.jar" "$DQC_HOME/lib/boot" "$DQC_HOME/lib" `"
		
		verbrun \
			"$JAVA_EXE" \
			-cp "$CLASSPATH" \
			$JAVA_OPTS \
			"com.ataccama.dqc.bootstrap.DqcBootstrap" \
			"$DQC_HOME" \
			"$CLASS" \
			"$@"
	;;
	local:1)
		addToClasspath "` findGlobFirst "cif[.-]commons*.jar" "$DQC_HOME/lib" `"

		verbrun \
			"$JAVA_EXE" \
			-cp "$CLASSPATH" \
			$JAVA_OPTS \
			"com.ataccama.dqc.commons.launch.RunnerMain" \
			"$PROP_FILE" \
			"$CLASS" \
			-execType=l \
			"$@"
	;;
	mr:0)
		addToClasspath "` findGlobFirst "cif[.-]hadoop[.-]boot*.jar" "$DQC_HOME/lib/boot" "$DQC_HOME/lib" `"
		
		verbrun \
			"$JAVA_EXE" \
			-cp "$CLASSPATH" \
			$JAVA_OPTS \
			"com.ataccama.dqc.hadoop.launcher.HadoopLauncher" \
			"$PROP_FILE" \
			"$CLASS" \
			"$@"
	;;
	mr:1)
		addToClasspath "` findGlobFirst "cif[.-]commons*.jar" "$DQC_HOME/lib" `"

		verbrun \
			"$JAVA_EXE" \
			-cp "$CLASSPATH" \
			$JAVA_OPTS \
			"com.ataccama.dqc.commons.launch.RunnerMain" \
			"$PROP_FILE" \
			"$CLASS" \
			-execType=m \
			"$@"
	;;
	spark:0)
		# signed BC must be before the Spark JAR
		addToClasspath "$DQC_HOME/lib/"bcp*.jar
		addToClasspath "$SPARK_HOME/lib/"spark-assembly-*.jar "$SPARK_HOME/lib/"datanucleus-*.jar
		addToClasspath "` findGlobFirst "cif[.-]hadoop[.-]boot*.jar" "$DQC_HOME/lib/boot" "$DQC_HOME/lib" `"
	
		verbrun \
			"$JAVA_EXE" \
			-cp "$CLASSPATH" \
			$JAVA_OPTS \
			"com.ataccama.dqc.hadoop.launcher.HadoopLauncher" \
			"$PROP_FILE" \
			"$CLASS" \
			"$@"
	;;
	spark:1)
		addToClasspath "` findGlobFirst "cif[.-]commons*.jar" "$DQC_HOME/lib" `"
		
		verbrun \
			"$JAVA_EXE" \
			-cp "$CLASSPATH" \
			$JAVA_OPTS \
			"com.ataccama.dqc.commons.launch.RunnerMain" \
			"$PROP_FILE" \
			"$CLASS" \
			-execType=s \
			"$@"
	;;
	*)
		errecho "The mode $MODE is not supported."
		exit 1
	;;
esac