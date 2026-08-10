{\rtf1\ansi\ansicpg1252\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 ---\
id: US-521b\
title: Guia de ambiente local reproducible \'97 Airflow y jobs ML\
owner: Edgar Jimenez\
sprint: S1\
status: In Progress\
date: 2026-08-09\
---\
\
# Gu\'eda de Ambiente Local Reproducible\
\
Este documento detalla la configuraci\'f3n local para correr Airflow y los jobs de Machine Learning (MLflow) de manera aislada y controlada.\
\
## 1. Mapeo de Puertos\
Para evitar conflictos en la m\'e1quina local, se han asignado los siguientes puertos:\
* **Airflow Webserver:** Puerto `8080`\
* **MLflow Tracking Server:** Puerto `5000`\
\
## 2. Variables de Entorno\
Las variables se encuentran declaradas en el archivo `configuracion.env` en la ra\'edz del componente:\
* `AIRFLOW_PORT`: Puerto de acceso a la interfaz de Airflow.\
* `MLFLOW_PORT`: Puerto de acceso a la interfaz de MLflow.\
* `MLFLOW_TRACKING_URI`: Direcci\'f3n local para el registro de experimentos de ML.\
\
## 3. Verificaci\'f3n del Entorno\
Una vez levantados los servicios, la validaci\'f3n se realiza ingresando desde el navegador web a las URL locales de cada puerto correspondiente.\
}