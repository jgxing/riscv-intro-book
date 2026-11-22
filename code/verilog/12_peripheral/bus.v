module bus (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] addr,
    input  wire        we,
    input  wire [2:0]  funct3,
    input  wire [31:0] wdata,
    input  wire [7:0]  switch_i,
    input  wire [7:0]  rx_i,
    input  wire        rx_valid_i,
    output wire [7:0]  led_o,
    output wire [7:0]  tx_o,
    output wire        tx_valid_o,
    output wire [31:0] rdata
);

    localparam [31:0] MEM_BASE   = 32'h10000000;
    localparam [31:0] MEM_MASK   = 32'hfffff000;

    wire mem_sel = ((addr & MEM_MASK) == MEM_BASE);
    wire io_sel  = (addr[31:16] == 16'hffff);

    wire dmem_we = we & mem_sel;
    wire gpio_we = we & io_sel;
    wire uart_we = we & io_sel;

    wire [31:0] dmem_rdata;
    wire [31:0] gpio_rdata;
    wire [31:0] uart_rdata;
    wire [31:0] timer_rdata;

    dmem u_dmem (
        .clk    (clk),
        .addr   (addr),
        .we     (dmem_we),
        .funct3 (funct3),
        .wdata  (wdata),
        .rdata  (dmem_rdata)
    );

    gpio u_gpio (
        .clk       (clk),
        .rst_n     (rst_n),
        .addr      (addr),
        .we        (gpio_we),
        .wdata     (wdata),
        .switch_i  (switch_i),
        .led_o     (led_o),
        .rdata     (gpio_rdata)
    );

    uart u_uart (
        .clk         (clk),
        .rst_n       (rst_n),
        .addr        (addr),
        .we          (uart_we),
        .wdata       (wdata),
        .rx_i        (rx_i),
        .rx_valid_i  (rx_valid_i),
        .tx_o        (tx_o),
        .tx_valid_o  (tx_valid_o),
        .rdata       (uart_rdata)
    );

    timer u_timer (
        .clk   (clk),
        .rst_n (rst_n),
        .addr  (addr),
        .rdata (timer_rdata)
    );

    assign rdata = mem_sel ? dmem_rdata :
                   io_sel  ? (gpio_rdata | uart_rdata | timer_rdata) : 32'b0;

endmodule
