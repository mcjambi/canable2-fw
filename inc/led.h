#ifndef _LED_H
#define _LED_H

// GPIO definitions
#define LED_BLUE_Pin GPIO_PIN_15
#define LED_BLUE_Port GPIOA
#define LED_BLUE LED_BLUE_Port , LED_BLUE_Pin

#define LED_GREEN_Pin GPIO_PIN_11
#define LED_GREEN_Port GPIOB
#define LED_GREEN LED_GREEN_Port , LED_GREEN_Pin


// Duration of LED blink
#define LED_DURATION 25


// Prototypes
void led_init();
void led_blue_blink(uint8_t numblinks);
void led_green_on(void);
void led_green_off(void);
void led_blue_on(void);
void led_process(void);
// 🔥 Thêm khai báo hàm cho PA5
void led_pa5_blink(void);

#endif
