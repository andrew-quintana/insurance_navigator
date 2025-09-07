# Page snapshot

```yaml
- generic [ref=e1]:
  - alert [ref=e2]
  - generic [ref=e3]:
    - banner [ref=e4]:
      - generic [ref=e5]:
        - link "Return to Home" [ref=e6] [cursor=pointer]:
          - /url: /
          - img [ref=e7] [cursor=pointer]
          - generic [ref=e9] [cursor=pointer]: Return to Home
        - heading "Sign In" [level=1] [ref=e10]
    - generic [ref=e12]:
      - generic [ref=e13]:
        - heading "Welcome Back" [level=2] [ref=e14]
        - paragraph [ref=e15]: Sign in to your Medicare Navigator account
      - generic [ref=e16]:
        - generic [ref=e17]:
          - generic [ref=e18]: Email Address
          - generic [ref=e19]:
            - img [ref=e20]
            - textbox "Email Address" [ref=e23]: frontend_test_1757280001708@example.com
        - generic [ref=e24]:
          - generic [ref=e25]: Password
          - generic [ref=e26]:
            - img [ref=e27]
            - textbox "Password" [active] [ref=e30]: test_password_123
            - button [ref=e31] [cursor=pointer]:
              - img [ref=e32] [cursor=pointer]
        - button "Sign In" [ref=e35] [cursor=pointer]
      - link "Forgot your password?" [ref=e37] [cursor=pointer]:
        - /url: /forgot-password
      - paragraph [ref=e39]:
        - text: Don’t have an account?
        - link "Sign up here" [ref=e40] [cursor=pointer]:
          - /url: /register
```