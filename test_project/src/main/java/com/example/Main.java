package com.example;

public class Main {
    public static void main(String[] args) {
        UserService userService = new UserService();
        User user = new User("testUser", "test@example.com", 25);
        userService.addUser(user);
        System.out.println(userService.getUsers());
    }
} 