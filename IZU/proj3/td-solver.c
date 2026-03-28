#include <stdio.h>

int get_reward(int item){
    if (item == 9) return 1;
    if(item == 12) return -1;
    return 0;
}

int main(){

    double grid[20] = {
        -0.086,  0.007,  0.132,  0.349,  0.366,
        -0.188, -0.483,  0.049,  0.000,  0.560,
        -0.190,  0.000, -0.266,  0.110,  0.253,
        -0.137, -0.263, -0.061,  0.083,  0.120
    };

    int path[12] = {1, 2, 3, 4, 5, 10, 15, 20, 19, 14, 13, 12};

    double alpha = 0.2;
    double gamma = 0.7;

    for(int t = 0; t < 11; t++) {
        int state = path[t];      
        int state_next = path[t+1]; 
        
        int index = state - 1;
        int index_next = state_next - 1;

        double r = get_reward(state_next);
        
        grid[index] = grid[index] + alpha * (r + gamma * grid[index_next] - grid[index]);
    }

    for(int i = 0;i<20;++i){
        printf("%.3f ", grid[i]);
        if(i == 4 || i == 9 || i == 14 || i ==19) 
            printf("\n");
    }

    return 0;
}