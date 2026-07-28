import streamlit as st
import requests

API_BASE = "http://localhost:8000"


def api_get(endpoint: str) -> requests.Response:
    return requests.get(f"{API_BASE}{endpoint}")


def api_post(endpoint: str, json: dict) -> requests.Response:
    return requests.post(f"{API_BASE}{endpoint}", json=json)