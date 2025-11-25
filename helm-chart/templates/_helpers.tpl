{{/*
Expand the name of the chart.
*/}}
{{- define "enabler.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "enabler.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "enabler.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Name of the component hardwareinfo.
*/}}
{{- define "hardwareinfo.name" -}}
{{- printf "%s-hardwareinfo" (include "enabler.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified component hardwareinfo name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "hardwareinfo.fullname" -}}
{{- printf "%s-hardwareinfo" (include "enabler.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Component hardwareinfo labels.
*/}}
{{- define "hardwareinfo.labels" -}}
helm.sh/chart: {{ include "enabler.chart" . }}
{{ include "hardwareinfo.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Component hardwareinfo selector labels.
*/}}
{{- define "hardwareinfo.selectorLabels" -}}
app.kubernetes.io/name: {{ include "enabler.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: hardwareinfo
isMainInterface: "yes"
tier: {{ .Values.hardwareinfo.tier }}
{{- end }}

{{/*
Name of the component powerconsumptionamd64.
*/}}
{{- define "powerconsumptionamd64.name" -}}
{{- printf "%s-powerconsumptionamd64" (include "enabler.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified component powerconsumptionamd64 name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "powerconsumptionamd64.fullname" -}}
{{- printf "%s-powerconsumptionamd64" (include "enabler.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Component powerconsumptionamd64 labels.
*/}}
{{- define "powerconsumptionamd64.labels" -}}
helm.sh/chart: {{ include "enabler.chart" . }}
{{ include "powerconsumptionamd64.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Component powerconsumptionamd64 selector labels.
*/}}
{{- define "powerconsumptionamd64.selectorLabels" -}}
app.kubernetes.io/name: {{ include "enabler.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: powerconsumptionamd64
isMainInterface: "no"
tier: {{ .Values.powerconsumptionamd64.tier }}
{{- end }}

{{/*
Name of the component powerconsumptionarm64.
*/}}
{{- define "powerconsumptionarm64.name" -}}
{{- printf "%s-powerconsumptionarm64" (include "enabler.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified component powerconsumptionarm64 name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "powerconsumptionarm64.fullname" -}}
{{- printf "%s-powerconsumptionarm64" (include "enabler.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Component powerconsumptionarm64 labels.
*/}}
{{- define "powerconsumptionarm64.labels" -}}
helm.sh/chart: {{ include "enabler.chart" . }}
{{ include "powerconsumptionarm64.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Component powerconsumptionarm64 selector labels.
*/}}
{{- define "powerconsumptionarm64.selectorLabels" -}}
app.kubernetes.io/name: {{ include "enabler.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: powerconsumptionarm64
isMainInterface: "no"
tier: {{ .Values.powerconsumptionarm64.tier }}
{{- end }}

