use workflowsdb;
CREATE TABLE `Inputs` (
	`workflow_id` varchar(255) NOT NULL DEFAULT '',
	`path` varchar(255) NOT NULL DEFAULT '',
	`processor` varchar(255) NOT NULL DEFAULT '',
	`type` varchar(50) DEFAULT NULL,
	PRIMARY KEY (`workflow_id`,`path`,`processor`)
) ENGINE=innodb DEFAULT CHARSET=latin1;

CREATE TABLE `Outputs` (
	`workflow_id` varchar(255) NOT NULL DEFAULT '',
	`path` varchar(400) NOT NULL DEFAULT '',
	`processor` varchar(255) NOT NULL DEFAULT '',
	`type` varchar(50) DEFAULT NULL,
	`port` varchar(255) DEFAULT NULL,
	PRIMARY KEY (`workflow_id`,`path`,`processor`)
) ENGINE=innodb DEFAULT CHARSET=latin1;

CREATE TABLE `Processors` (
	`workflow_id` varchar(255) NOT NULL DEFAULT '',
	`processor` varchar(255) NOT NULL DEFAULT '',
	`completed` int(11) DEFAULT NULL,
	`queued` int(11) DEFAULT NULL,
	`failed` int(11) DEFAULT NULL,
	PRIMARY KEY (`workflow_id`,`processor`)
) ENGINE=innodb DEFAULT CHARSET=latin1;

CREATE TABLE `Stats` (
	`workflow_id` varchar(255) NOT NULL DEFAULT '',
	`completed` int(11) DEFAULT NULL,
	`completed_wt` bigint(20) DEFAULT NULL,
	`completed_et` bigint(20) DEFAULT NULL,
	`completed_it` bigint(20) DEFAULT NULL,
	`completed_ot` bigint(20) DEFAULT NULL,
	`cancelled` int(11) DEFAULT NULL,
	`cancelled_wt` bigint(20) DEFAULT NULL,
	`cancelled_et` bigint(20) DEFAULT NULL,
	`cancelled_it` bigint(20) DEFAULT NULL,
	`cancelled_ot` bigint(20) DEFAULT NULL,
	`failed_app` int(11) DEFAULT NULL,
	`failed_app_wt` bigint(20) DEFAULT NULL,
	`failed_app_et` bigint(20) DEFAULT NULL,
	`failed_app_it` bigint(20) DEFAULT NULL,
	`failed_app_ot` bigint(20) DEFAULT NULL,
	`failed_in` int(11) DEFAULT NULL,
	`failed_in_wt` bigint(20) DEFAULT NULL,
	`failed_in_et` bigint(20) DEFAULT NULL,
	`failed_in_it` bigint(20) DEFAULT NULL,
	`failed_in_ot` bigint(20) DEFAULT NULL,
	`failed_out` int(11) DEFAULT NULL,
	`failed_out_wt` bigint(20) DEFAULT NULL,
	`failed_out_et` bigint(20) DEFAULT NULL,
	`failed_out_it` bigint(20) DEFAULT NULL,
	`failed_out_ot` bigint(20) DEFAULT NULL,
	`failed_sta` int(11) DEFAULT NULL,
	`failed_sta_wt` bigint(20) DEFAULT NULL,
	`failed_sta_et` bigint(20) DEFAULT NULL,
	`failed_sta_it` bigint(20) DEFAULT NULL,
	`failed_sta_ot` bigint(20) DEFAULT NULL,
	PRIMARY KEY (`workflow_id`)
) ENGINE=innodb DEFAULT CHARSET=latin1;

CREATE TABLE `Workflows` (
	`id` varchar(255) NOT NULL DEFAULT '',
	`username` varchar(255) DEFAULT NULL,
	`status` varchar(50) DEFAULT NULL,
	`launched` timestamp NULL DEFAULT NULL,
	`finish_time` timestamp NULL DEFAULT NULL,
	`simulation_name` varchar(255) DEFAULT NULL,
	`application` varchar(255) DEFAULT NULL,
	`application_version` varchar(255) DEFAULT NULL,
	`application_class` varchar(255) DEFAULT NULL,
	`engine` varchar(255) DEFAULT NULL,
	PRIMARY KEY (`id`)
) ENGINE=innodb DEFAULT CHARSET=latin1;
