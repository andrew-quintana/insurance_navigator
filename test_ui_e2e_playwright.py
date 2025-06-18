#!/usr/bin/env python3
"""
Playwright UI End-to-End Test for Insurance Navigator
=====================================================
Tests the complete UI workflow including:
1. Page loading
2. Document upload UI
3. Chat interface
4. Navigation
"""

import asyncio
from playwright.async_api import async_playwright
import tempfile
import uuid
import json
from datetime import datetime
import os
from pathlib import Path

class UIEndToEndTest:
    def __init__(self):
        self.base_url = "http://localhost:3000"  # Default Next.js dev server
        self.test_results = []
        self.test_session_id = f"ui-test-{uuid.uuid4().hex[:8]}"
        
    async def run_ui_tests(self):
        """Run complete UI test suite"""
        print("🌐 Insurance Navigator - UI End-to-End Test")
        print("=" * 55)
        print(f"🆔 Test Session: {self.test_session_id}")
        print(f"🔗 Base URL: {self.base_url}")
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False)  # Set True for CI
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Test 1: Homepage Load
                await self.test_homepage_load(page)
                
                # Test 2: Authentication Flow
                await self.test_authentication_flow(page)
                
                # Test 3: Document Upload UI
                await self.test_document_upload_ui(page)
                
                # Test 4: Chat Interface
                await self.test_chat_interface(page)
                
                # Test 5: Navigation
                await self.test_navigation(page)
                
                # Generate Report
                self.generate_ui_test_report()
                
            except Exception as e:
                print(f"❌ Critical UI test failure: {e}")
                self.test_results.append({
                    "test": "Critical UI Failure",
                    "status": "FAILED",
                    "error": str(e)
                })
            finally:
                await browser.close()
    
    async def test_homepage_load(self, page):
        """Test 1: Homepage Loading"""
        print("\n🏠 Test 1: Homepage Load")
        print("-" * 30)
        
        try:
            # Navigate to homepage
            response = await page.goto(self.base_url, wait_until="networkidle")
            
            if response and response.status == 200:
                print("✅ Homepage loaded successfully")
                
                # Check for key elements
                title = await page.title()
                print(f"📄 Page title: {title}")
                
                # Look for common UI elements
                elements_to_check = [
                    'h1, h2, .title',  # Main heading
                    'nav, .navigation',  # Navigation
                    'button, .btn',  # Buttons
                ]
                
                found_elements = 0
                for selector in elements_to_check:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            found_elements += 1
                            text = await element.text_content()
                            print(f"   ✅ Found: {selector} - '{text[:30]}...'")
                    except:
                        continue
                
                self.test_results.append({
                    "test": "Homepage Load", 
                    "status": "PASSED",
                    "details": f"Status {response.status}, {found_elements} UI elements found"
                })
                
            else:
                status = response.status if response else "No response"
                raise Exception(f"Homepage failed to load: {status}")
                
        except Exception as e:
            print(f"❌ Homepage load failed: {e}")
            self.test_results.append({
                "test": "Homepage Load",
                "status": "FAILED", 
                "error": str(e)
            })
    
    async def test_authentication_flow(self, page):
        """Test 2: Authentication Flow"""
        print("\n🔐 Test 2: Authentication Flow")
        print("-" * 30)
        
        try:
            # Look for login/register links
            auth_selectors = [
                'a[href*="login"]',
                'a[href*="register"]', 
                'a[href*="sign"]',
                '.login-btn',
                '.auth-button'
            ]
            
            auth_found = False
            for selector in auth_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        print(f"✅ Found auth element: {text}")
                        auth_found = True
                        
                        # Try clicking (but don't complete auth for now)
                        await element.click()
                        await page.wait_for_timeout(1000)  # Wait 1 second
                        
                        current_url = page.url
                        print(f"📍 Navigated to: {current_url}")
                        
                        # Go back to home
                        await page.goto(self.base_url)
                        break
                except:
                    continue
            
            if auth_found:
                self.test_results.append({
                    "test": "Authentication Flow",
                    "status": "PASSED",
                    "details": "Auth elements found and clickable"
                })
            else:
                print("⚠️ No authentication elements found")
                self.test_results.append({
                    "test": "Authentication Flow",
                    "status": "PARTIAL",
                    "details": "No auth elements found - may be already authenticated"
                })
                
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            self.test_results.append({
                "test": "Authentication Flow",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_document_upload_ui(self, page):
        """Test 3: Document Upload UI"""
        print("\n📤 Test 3: Document Upload UI")
        print("-" * 30)
        
        try:
            # Look for upload-related elements
            upload_selectors = [
                'input[type="file"]',
                '.upload-area',
                '.dropzone',
                'button[data-upload]',
                '[data-testid*="upload"]'
            ]
            
            upload_found = False
            for selector in upload_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"✅ Found upload element: {selector}")
                        upload_found = True
                        
                        # If it's a file input, test with a temporary file
                        if selector == 'input[type="file"]':
                            # Create a test file
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                                f.write(f"Test upload file - {self.test_session_id}")
                                test_file_path = f.name
                            
                            try:
                                # Set the file
                                await element.set_input_files(test_file_path)
                                print(f"✅ File selected: {Path(test_file_path).name}")
                                
                                # Look for upload button
                                upload_btn = await page.query_selector('button[type="submit"], .upload-btn, [data-upload-btn]')
                                if upload_btn:
                                    print("✅ Upload button found (not clicking in test)")
                                
                            finally:
                                # Clean up test file
                                os.unlink(test_file_path)
                        
                        break
                except:
                    continue
            
            if upload_found:
                self.test_results.append({
                    "test": "Document Upload UI",
                    "status": "PASSED",
                    "details": "Upload UI elements found and functional"
                })
            else:
                print("⚠️ No upload UI elements found")
                self.test_results.append({
                    "test": "Document Upload UI",
                    "status": "FAILED",
                    "details": "No upload UI elements found"
                })
                
        except Exception as e:
            print(f"❌ Upload UI test failed: {e}")
            self.test_results.append({
                "test": "Document Upload UI",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_chat_interface(self, page):
        """Test 4: Chat Interface"""
        print("\n💬 Test 4: Chat Interface")
        print("-" * 30)
        
        try:
            # Look for chat-related elements
            chat_selectors = [
                '.chat-container',
                '.chat-window',
                'input[placeholder*="message"]',
                'input[placeholder*="chat"]',
                'textarea[placeholder*="message"]',
                '[data-testid*="chat"]'
            ]
            
            chat_found = False
            for selector in chat_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"✅ Found chat element: {selector}")
                        chat_found = True
                        
                        # If it's an input, test typing
                        if 'input' in selector or 'textarea' in selector:
                            test_message = f"Test message from UI E2E - {self.test_session_id}"
                            await element.fill(test_message)
                            print(f"✅ Typed test message: {test_message[:30]}...")
                            
                            # Clear the input
                            await element.fill("")
                        
                        break
                except:
                    continue
            
            if chat_found:
                self.test_results.append({
                    "test": "Chat Interface",
                    "status": "PASSED",
                    "details": "Chat UI elements found and functional"
                })
            else:
                print("⚠️ No chat UI elements found")
                self.test_results.append({
                    "test": "Chat Interface",
                    "status": "PARTIAL", 
                    "details": "No chat UI elements found - may require authentication"
                })
                
        except Exception as e:
            print(f"❌ Chat interface test failed: {e}")
            self.test_results.append({
                "test": "Chat Interface",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_navigation(self, page):
        """Test 5: Navigation"""
        print("\n🧭 Test 5: Navigation")
        print("-" * 30)
        
        try:
            # Look for navigation links
            nav_selectors = [
                'nav a',
                '.nav-link',
                '.menu-item',
                'a[href="/"]',
                'a[href*="chat"]',
                'a[href*="upload"]',
                'a[href*="dashboard"]'
            ]
            
            nav_links = []
            for selector in nav_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute('href')
                        text = await element.text_content()
                        if href and text:
                            nav_links.append({"href": href, "text": text.strip()})
                except:
                    continue
            
            if nav_links:
                print(f"✅ Found {len(nav_links)} navigation links:")
                for link in nav_links[:5]:  # Show first 5
                    print(f"   📎 {link['text']} → {link['href']}")
                
                # Test one navigation link
                if nav_links:
                    test_link = nav_links[0]
                    link_element = await page.query_selector(f'a[href="{test_link["href"]}"]')
                    if link_element:
                        await link_element.click()
                        await page.wait_for_timeout(1000)
                        print(f"✅ Successfully navigated to: {page.url}")
                
                self.test_results.append({
                    "test": "Navigation",
                    "status": "PASSED",
                    "details": f"{len(nav_links)} nav links found and functional"
                })
            else:
                print("⚠️ No navigation links found")
                self.test_results.append({
                    "test": "Navigation",
                    "status": "FAILED",
                    "details": "No navigation links found"
                })
                
        except Exception as e:
            print(f"❌ Navigation test failed: {e}")
            self.test_results.append({
                "test": "Navigation",
                "status": "FAILED",
                "error": str(e)
            })
    
    def generate_ui_test_report(self):
        """Generate UI test report"""
        print("\n📊 UI End-to-End Test Report")
        print("=" * 45)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed = len([r for r in self.test_results if r['status'] == 'FAILED']) 
        partial = len([r for r in self.test_results if r['status'] == 'PARTIAL'])
        
        print(f"📈 Summary: {passed} passed, {failed} failed, {partial} partial")
        print(f"🆔 Test Session: {self.test_session_id}")
        print(f"⏰ Completed: {datetime.now().isoformat()}")
        
        for result in self.test_results:
            if result['status'] == 'PASSED':
                emoji = "✅"
            elif result['status'] == 'FAILED':
                emoji = "❌"
            else:
                emoji = "⚠️"
                
            print(f"   {emoji} {result['test']}: {result['status']}")
            
            if 'details' in result:
                print(f"      Details: {result['details']}")
            if 'error' in result:
                print(f"      Error: {result['error']}")

async def main():
    """Run UI end-to-end tests"""
    ui_test = UIEndToEndTest()
    await ui_test.run_ui_tests()

if __name__ == "__main__":
    print("🎭 Starting Playwright UI Tests...")
    print("⚠️ Make sure your Next.js dev server is running on localhost:3000")
    print("   Run: cd ui && npm run dev")
    print()
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Failed to run UI tests: {e}")
        print("💡 Make sure Playwright is installed: pip install playwright && playwright install") 