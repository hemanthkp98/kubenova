{{/*
KubeNova Helm chart helpers.
*/}}

{{/* Expand the name of the chart. */}}
{{- define "kubenova.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Create a default fully qualified app name. */}}
{{- define "kubenova.fullname" -}}
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

{{/* Create chart name and version as used by the chart label. */}}
{{- define "kubenova.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels */}}
{{- define "kubenova.labels" -}}
helm.sh/chart: {{ include "kubenova.chart" . }}
{{ include "kubenova.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Selector labels */}}
{{- define "kubenova.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kubenova.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* Backend selector labels */}}
{{- define "kubenova.backendSelectorLabels" -}}
app.kubernetes.io/name: {{ include "kubenova.name" . }}-backend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* Frontend selector labels */}}
{{- define "kubenova.frontendSelectorLabels" -}}
app.kubernetes.io/name: {{ include "kubenova.name" . }}-frontend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* Service account name */}}
{{- define "kubenova.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "kubenova.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
